import argparse
import sys
import requests
import json

parser = argparse.ArgumentParser()
parser.add_argument("username", help="The username")
parser.add_argument("password", help="The password")
args = parser.parse_args()

payload = {"client_id" : "f2pQL6jMgGQLDsNlHfhQgsmMVGzMcgmg",
	"username" : args.username,
	"password" : args.password,
	"id_token" : "null",
	"connection" : "Username-Password-Authentication",
	"grant_type" : "password",
	"scope" : "openid",
	"device" : "null"}
	
loginRequest = requests.get('https://enel500blockvote.auth0.com/oauth/ro', data = payload)

if loginRequest.ok:
	r=loginRequest.json()
	id_token="Bearer "+r['id_token']
	access_token=r['access_token']

	header = {"Authorization" : id_token,
		"AccessToken" : access_token}
		
	initRequest = requests.get('https://blockvotenode2.mybluemix.net/init', headers = header)
	print(initRequest.text)
else:
	print("Could not login to Auth0")