import praw
import sys
import time
import signal
import os

# Globally create a user agent and our reddit object
user_agent = ("Print the posts from my stupid dumb subreddit") 
r = praw.Reddit(user_agent=user_agent)
r.login('c_zer0', 'hello1')

# isSerQuery - determing whether a comment is a SerBot query
# @param - comment_body, the body of text to determine
# @return - isSerBot, whether the comment is a SerBot request
def isSerQuery(comment_body):
	serBotStr = comment_body[0:6]
	termsStr = comment_body[7:12]
	secondCol = find_nth(comment_body,':',2)
	subredditStr = comment_body[secondCol - 10 : secondCol]

	isSerBot = 0
	if serBotStr == "SerBot" and termsStr == "Terms" and subredditStr == "Subreddits":
		isSerBot = 1

	return isSerBot

# find_nth - find the n'th occurence of a term inside a string
# @param - word, the word in which to search
# @param - term, the term to search for inside of word
# @n - the 'n'th occurence to find
# @return - start, the index of where the term begins
def find_nth(word, term, n):
	start = word.find(term)
	while start >= 0 and n > 1:
		start = word.find(term, start+len(term))
		n -= 1
	return start

# parseComment - read a comment body, check if it is a SerBot query then format the comment properly
# to be used in the search
# @param - comment_body, the body of text of the comment to parse
# @return - isSerBot, whether the comment is a SerBot query
# @return - theTermsFormatted, a list of the search terms
# @return - theSubsFormatted, a list of the subreddits to search
def parseComment(comment_body):
	serBotStr = comment_body[0:6]
	termsStr = comment_body[7:12]
	secondCol = find_nth(comment_body,':',2)
	subredditStr = comment_body[secondCol - 10 : secondCol]

	isSerBot = 0
	if serBotStr == "SerBot" and termsStr == "Terms" and subredditStr == "Subreddits":
		isSerBot = 1

	if(isSerBot):
		theTerms = comment_body[13:secondCol-11].split(',')
		theTermsFormatted = []
		for words in theTerms:
			words = words.strip()
			theTermsFormatted.append(words)

		theSubs = comment_body[secondCol+1:].split(',')
		theSubsFormatted = []
		for words in theSubs:
			words = words.strip()
			theSubsFormatted.append(words)

		return isSerBot, theTermsFormatted, theSubsFormatted

	return 0, [], []


# read_comments_sub - read the comments from my subreddit and check if there are any serBot
# queries, if a query is found, serve that query
#
# NOTE: This function should truly be inside a loop which runs it every set interval
# this functionaility however is not included because there is no server to run this bot on
def read_comments_sub():
	subreddit = r.get_subreddit("mypytest")
	for submission in subreddit.get_new(limit = 10):
		flat_comments = praw.helpers.flatten_tree(submission.comments)
		for comment in flat_comments:
			comment_text = comment.body
			author = comment.author
			userName = author.name
			serBotQuery, theTerms, theSubs = parseComment(comment_text)
			if(serBotQuery == 1):
				search(theSubs, theTerms, userName)



#def get_comments_file():
#	comments_done_file = open("done.txt", "r")
#	comments_done_list = comments_done_file.read().splitlines()
#	return comments_done_list


# search - a function designed to take a list of subreddits and search terms
# and match the terms and reply to the user with any hits
#
# @param - userSubRed, a list containing the subreddits to search
# @param - userSearchTerms, a list containing the search terms
# @param - userName, the username of the user who made the query
# return - nothing to be returned from this function

def search(userSubred, userSearchTerms, userName):
	# A list to hold the messages that will actully be sent back to the user
	searchPostResList = []
	postURL = []

	searchCommentResList = []
	commentURL = []

	# A string that combines all the search results
	totalRetStr = ''

	# Whether we actually have any results
	foundFlag = 0

	# Loop through the subreddits and each comment or post in the subreddits
	for subname in userSubred:
		subreddit = r.get_subreddit(subname)
		try:
			for submission in subreddit.get_new(limit = 100):
				# Get the data about the post (text, title)
				title = submission.title.lower()
				post_text = submission.selftext.lower()
				hasTermsInPost = 0;
				foundTermsInPost = []
				count = 0
				# For each term search through the post and post title
				for term in userSearchTerms:
					count = count + 1
					if (term in post_text.split() or term in title.split()):
						hasTermsInPost = 1
						foundFlag = 1
						foundTermsInPost.append(count)			
				if(hasTermsInPost):
					searchPostResList.append(foundTermsInPost) # The indexes of the found terms
					postURL.append(submission.short_link) # The URL

				# Check the comments

				flat_comments = praw.helpers.flatten_tree(submission.comments)
				for comment in flat_comments:
					# Get the author of the comment and get their name
					# if it is the bot ignore their comment. We dont want the bots comments
					# or if the comment was made by the user who actually generated the query
					author = comment.author
					if(author.name == 'c_zer0___' or isSerQuery(comment.body)):
						continue
					hasTermsInComment = 0
					foundTermsInComment = []
					count_comment = 0
					# For each term, search through the comments
					for term in userSearchTerms:
						count_comment = count_comment + 1
						comment_text = comment.body.lower()
						if (term in comment_text.split()):
							foundFlag = 1
							hasTermsInComment = 1
							foundTermsInComment.append(count_comment)
					if(hasTermsInComment):
						searchCommentResList.append(foundTermsInComment)
						commentURL.append(comment.permalink)

			
			# Create the message that we will actually send to the user containing their search results

			postUrlCount = 0
			for lists in searchPostResList:
				theTermsFound = 'The term(s) found are :  '
				for items in lists:
					theTermsFound += userSearchTerms[items-1] + ","
				totalRetStr += theTermsFound + " found in the following post(s) : " + postURL[postUrlCount] + "\n"
				postUrlCount = postUrlCount + 1

			commentUrlCount = 0
			for lists in searchCommentResList:
				theTermsFound = 'The term(s) found are : '
				for items in lists:
					theTermsFound += userSearchTerms[items-1] + ","
				totalRetStr += theTermsFound + " found in the following comment(s) : " + commentURL[commentUrlCount] + "\n"
				commentUrlCount = commentUrlCount + 1

			

		# If the subreddit name does not exist, dont cease operations
		# simply remove this subreddit from the list of candidates
		except praw.errors.RedirectException:
			print "The entered subreddit does not appear to exist"
			print "It will be removed from the list"
			userSubred.remove(subname)

	print totalRetStr

	# If we found anything, send the user a message with the results
	if(foundFlag):
		r.send_message(userName, "Search Results", totalRetStr)
		
#------------------ End Main ------------------#
read_comments_sub()
