import json
import requests
import datetime

class RepositoryStatistics(object):
    def __init__(self,repositoryData):
        maxCommitSingleUser,minCommitSingleUser = repositoryData.getMaxMinCommitSingleUser

        self.averageAdditions = repositoryData.totalAdditions / repositoryData.amountOfCommits
        self.averageDeletions = repositoryData.totalDeletions / repositoryData.amountOfCommits
        self.averageMessageLength = repositoryData.totalMessageLength / repositoryData.amountOfCommits
        self.amountOfUsers = len(repositoryData.differentUsers)
        self.commitsPerUser = repositoryData.amountOfCommits / self.amountOfUsers
        self.commitDifferenceMaxMinusMin = maxCommitSingleUser - minCommitSingleUser
        self.averageDaysBetweenCommits = repositoryData.daysBetweenCommits / repositoryData.amountOfCommits
        self.lastCommitDaysBeforeDeadline = repositoryData.lastCommitDaysBeforeDeadline


class RepositoryData(object):
    def __init__(self):
        self.differentUsers = {}
        self.amountOfCommits = 0
        self.totalAdditions = 0
        self.totalDeletions = 0
        self.totalMessageLength = 0
        self.daysBetweenCommits = 0
        self.lastCommitDaysBeforeDeadline = -1

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
    print ("Commit message: %s.     Additions: %s. Deletions: %s" % (commit['commit']['message'],commit['stats']['additions'],commit['stats']['deletions']))

def start():
    user = 'ericzucho'
    repo = 'assignment2'
    branch = 'homework-solved'
    deadline = datetime.datetime(year=2016,month=9,day=18)

    repoData = RepositoryData()

    analyzeRepo(user,repo,branch,deadline,repoData)

    if repoData.amountOfCommits == 0:
        print("No commits.")
        return

    repoStatistics = RepositoryStatistics(repoData)


if __name__ == '__main__':
    start()