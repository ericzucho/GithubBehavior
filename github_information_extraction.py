import json

import pytz
import requests
import datetime
import iso8601
import pandas as pd
import numpy as np

class Commit(object):
    def __init__(self,additions,deletions,changes,amountOfFiles,userEmail,message,timestamp,repository):
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.amountOfFiles = amountOfFiles
        self.userEmail = userEmail
        self.message = message
        self.timestamp = timestamp
        self.repository = repository

    def asArray(self):
        return [self.additions,self.deletions,self.changes,self.amountOfFiles,self.userEmail,len(self.message),self.timestamp,self.repository]

    def asTuple(self):
        return (self.additions,self.deletions,self.changes,self.amountOfFiles,self.userEmail,len(self.message),self.timestamp,self.repository)

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
    def __init__(self,user,repo,branch):
        self.repository = user+"$"+repo+"$"+branch
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


def analyzeRepo(user,repo,branch,deadline,repositoryData):
    extractCommitFromURL('https://api.github.com/repos/%s/%s/commits/%s' % (user, repo, branch),deadline,repositoryData)

def extractCommitFromURL(url,deadline,repositoryData):
    r = requests.get(url)
    commit = json.loads(r.content)
    extractDataFromCommit(commit,deadline,repositoryData)
    if len(commit['parents']) > 0:
        extractCommitFromURL(commit['parents'][0]['url'],deadline,repositoryData)

def extractDataFromCommit(commit, deadline, repositoryData):
    if commit['commit']['committer']['email'] not in repositoryData.differentUsers:
        repositoryData.addNewUserToDictionary(commit['commit']['committer']['email'])
    else:
        repositoryData.addToExistingUserInDictionary(commit['commit']['committer']['email'])
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
    repositoryData.commitArray.append(Commit(commit['stats']['additions'],commit['stats']['deletions'],commit['stats']['total'],len(commit['files']),commit['commit']['committer']['email'],commit['commit']['message'],commitTimestamp,repositoryData.repository))

def start():
    user = 'ericzucho'
    repo = 'assignment2'
    branch = 'homework-solved'
    deadline = datetime.datetime(year=2016,month=9,day=18,tzinfo=pytz.timezone('US/Central'))

    repoData = RepositoryData(user,repo,branch)

    analyzeRepo(user,repo,branch,deadline,repoData)

    if repoData.amountOfCommits == 0:
        print("No commits.")
        return

    repoStatistics = RepositoryStatistics(repoData)
    repoStatistics

    bla = [i.asTuple() for i in repoData.commitArray]

    #numpyData = np.array([['','Additions','Deletions','Changes','AmountOfFiles','UserEmail','MessageLength','Timestamp','Repository'],
    #                      bla.flatten()])

    #pandasData = pd.DataFrame(data=numpyData[1:,1:],
    #              index=numpyData[1:,0],
    #              columns=numpyData[0,1:])

    columns = ['Additions','Deletions','Changes','AmountOfFiles','UserEmail','MessageLength','Timestamp','Repository']
    df = pd.DataFrame.from_records(bla,columns=columns)
    df

if __name__ == '__main__':
    start()

# PANDAS
