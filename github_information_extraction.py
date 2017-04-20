import json

import pytz
import requests
import datetime
import iso8601
import pandas as pd
import csv
import os.path

owner = "ericzucho"
password = "Erzz1692"

class Commit(object):
    def __init__(self,additions,deletions,changes,amountOfFiles,userEmail,message,timestamp,repository,repositoryOrganization,repositoryUsername):
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.amountOfFiles = amountOfFiles
        self.userEmail = userEmail
        self.message = message
        self.timestamp = timestamp
        self.repository = repository
        self.repositoryOrganization = repositoryOrganization
        self.repositoryUsername = repositoryUsername

    def asArray(self):
        return [self.additions,self.deletions,self.changes,self.amountOfFiles,self.userEmail,len(self.message),self.timestamp,self.repository,self.repositoryOrganization,self.repositoryUsername]

    def asTuple(self):
        return (self.additions,self.deletions,self.changes,self.amountOfFiles,self.userEmail,len(self.message),self.timestamp,self.repository,self.repositoryOrganization,self.repositoryUsername)

class RepositoryStatistics(object):
    def __init__(self,repositoryData):
        maxCommitSingleUser,minCommitSingleUser = repositoryData.getMaxMinCommitSingleUser()

        self.amountOfCommits = repositoryData.amountOfCommits
        self.averageAdditions = repositoryData.totalAdditions / repositoryData.amountOfCommits
        self.averageDeletions = repositoryData.totalDeletions / repositoryData.amountOfCommits
        self.averageChanges = repositoryData.totalChanges / repositoryData.amountOfCommits
        self.averageFilesChanged = repositoryData.totalFilesChanged / repositoryData.amountOfCommits
        self.averageMessageLength = repositoryData.totalMessageLength / repositoryData.amountOfCommits
        self.amountOfUsers = len(repositoryData.differentUsers)
        self.commitsPerUser = repositoryData.amountOfCommits / self.amountOfUsers
        self.commitDifferenceMaxMinusMin = maxCommitSingleUser - minCommitSingleUser
        self.averageDaysBetweenCommits = repositoryData.daysBetweenCommits / repositoryData.amountOfCommits
        self.lastCommitDaysBeforeDeadline = repositoryData.lastCommitDaysBeforeDeadline


class RepositoryData(object):
    def __init__(self,orgName,repoPrefix,branch):
        self.repository = repoPrefix
        self.repositoryOrganization = orgName
        self.repositoryUsername = branch
        self.differentUsers = {}
        self.amountOfCommits = 0
        self.totalAdditions = 0
        self.totalDeletions = 0
        self.totalChanges = 0
        self.totalFilesChanged = 0
        self.totalMessageLength = 0
        self.daysBetweenCommits = 0
        self.previousCommitDate = ''
        self.lastCommitDaysBeforeDeadline = -1
        self.commitArray = []

    def addNewUserToDictionary(self,user):
        self.differentUsers[user] = 1

    def addToExistingUserInDictionary(self,user):
        self.differentUsers[user] += 1

    def getMaxMinCommitSingleUser(self):
        minCommitSingleUser = 9999999
        maxCommitSingleUser = -1
        for k, v in self.differentUsers.items():
            if v > maxCommitSingleUser:
                maxCommitSingleUser = v
            if v < minCommitSingleUser:
                minCommitSingleUser = v
        return maxCommitSingleUser,minCommitSingleUser



def extractCommitFromURL(organization,repoPrefix,username,deadline,repositoryData):
    r = requests.get('https://api.github.com/repos/%s/%s-%s/commits' % (organization, repoPrefix, username), auth=(owner, password))
    if r.status_code != 200:
        return
    commits_sha = json.loads(r.content)
    for commit_sha in commits_sha:
        sha = commit_sha['sha']
        r2 = requests.get('https://api.github.com/repos/%s/%s-%s/commits/%s' % (organization, repoPrefix, username, sha), auth=(owner, password))
        commit = json.loads(r2.content)
        extractDataFromCommit(commit,deadline,repositoryData)


def extractDataFromCommit(commit, deadline, repositoryData):
    if commit['commit']['author']['name'] not in repositoryData.differentUsers:
        repositoryData.addNewUserToDictionary(commit['commit']['author']['name'])
    else:
        repositoryData.addToExistingUserInDictionary(commit['commit']['author']['name'])
    repositoryData.amountOfCommits += 1
    repositoryData.totalAdditions += commit['stats']['additions']
    repositoryData.totalDeletions += commit['stats']['deletions']
    repositoryData.totalChanges += commit['stats']['total']
    repositoryData.totalFilesChanged += len(commit['files'])
    repositoryData.totalMessageLength += len(commit['commit']['message'])
    commitTimestamp = iso8601.parse_date(commit['commit']['author']['date'])
    if repositoryData.lastCommitDaysBeforeDeadline == -1:
        repositoryData.lastCommitDaysBeforeDeadline = (deadline - commitTimestamp).days
    if repositoryData.previousCommitDate != '':
        repositoryData.daysBetweenCommits += (repositoryData.previousCommitDate - commitTimestamp).days
    repositoryData.previousCommitDate = commitTimestamp
    repositoryData.commitArray.append(Commit(commit['stats']['additions'],commit['stats']['deletions'],commit['stats']['total'],len(commit['files']),commit['commit']['author']['name'],commit['commit']['message'],commitTimestamp,repositoryData.repository,repositoryData.repositoryOrganization,repositoryData.repositoryUsername))



def start():

    columns = ['Additions','Deletions','Changes','AmountOfFiles','UserEmail','MessageLength','Timestamp','RepositoryName','RepositoryOwner','RepositoryBranch']

    with open('repos_input.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            deadline = datetime.datetime(year=2016,month=9,day=18,tzinfo=pytz.timezone('US/Central'))

            repoData = RepositoryData(row['Organization name'],row['Repo prefix'],row['Username'])

            extractCommitFromURL(row['Organization name'],row['Repo prefix'],row['Username'],deadline,repoData)

            if repoData.amountOfCommits == 0:
                print("No commits.")
                continue

            repoStatistics = RepositoryStatistics(repoData)
            repoStatistics

            repoDataAsTuple = [i.asTuple() for i in repoData.commitArray]

            df = pd.DataFrame.from_records(repoDataAsTuple,columns=columns)
            if os.path.isfile('output.csv'):
                with open('output.csv', 'a') as f:
                    df.to_csv(f, header=False)
            else:
                df.to_csv('output.csv')

if __name__ == '__main__':
    start()