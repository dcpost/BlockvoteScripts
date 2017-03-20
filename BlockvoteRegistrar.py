import argparse
import sys
import requests
import json
import base64
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
from subprocess import *

def jarWrapper(*args):
    process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE)
    ret = []
    while process.poll() is None:
        line = process.stdout.readline()
        if line != '' and line.endswith('\n'):
            ret.append(line[:-1])
    stdout, stderr = process.communicate()
    ret += stdout.split('\n')
    if stderr != '':
        ret += stderr.split('\n')
    ret.remove('')
    return ret
	
parser = argparse.ArgumentParser()
parser.add_argument("username", help="The admin username")
parser.add_argument("password", help="The admin password")
parser.add_argument("rname", help="The registrar name")
parser.add_argument("remail", help="The registrar email")
parser.add_argument("rpassword", help="The new password")
parser.add_argument("region", help="the region")
parser.add_argument("district", help="the registrar district")

args = parser.parse_args()

#Get API token
payload = {"grant_type":"client_credentials",
"client_id": "mjgRuEI10KlWWa7kAic7m6sD75FV0X81",
"client_secret": "gjNBs1NbFzX1xWw-zhBexGJpqZD-_hF0lK5Pg5H3yCSscx7bg-kZiLOJT3Ai5blt",
"audience": "https://enel500blockvote.auth0.com/api/v2/"
}

apiTokenRequest = requests.post("https://enel500blockvote.auth0.com/oauth/token", data = payload)
print(apiTokenRequest)
r=apiTokenRequest.json()
print(r)
api_token="Bearer "+r['access_token']

#Get the login info
payload = {"client_id" : "f2pQL6jMgGQLDsNlHfhQgsmMVGzMcgmg",
	"username" : args.username,
	"password" : args.password,
	"id_token" : "null",
	"connection" : "Username-Password-Authentication",
	"grant_type" : "password",
	"scope" : "openid",
	"device" : "null"}
	
loginRequest = requests.post('https://enel500blockvote.auth0.com/oauth/ro', data = payload)

r=loginRequest.json()
print(r)
id_token="Bearer "+r['id_token']
access_token=r['access_token']

#Create the api authorization header
Auth0Header = {"Authorization":api_token}
	
#generate key
javaargs = ['RSAGenerator.jar'] 
result = jarWrapper(*javaargs)
publicExponent = result[0].strip()
privateExponent = result[1].strip()
modulus = result[2].strip()

#Check if user exists
emailSearchString = "\""+args.remail+"\""
payload = {"page": "0",
  "fields": "email,user_id",
  "q": emailSearchString
  }

searchRequest = requests.get('https://enel500blockvote.auth0.com/api/v2/users', headers = Auth0Header,  params = payload)
r=searchRequest.json()
print(searchRequest)
print(r)
userExists = True
if len(r)<>1:
	userExists= False


if userExists:
	userID=r[0]["user_id"]
	payload = {
  "user_metadata": {
	  "publicKeyExponent": publicExponent,
	  "publicKeyModulus": modulus,
	  "privateKeyModulus": modulus,
	  "privateKeyExponent": privateExponent
	}
  }
  
	updateRequest = requests.patch('https://enel500blockvote.auth0.com/api/v2/users/'+userID, headers = Auth0Header,  json = payload)
	print(updateRequest)
	r=updateRequest.json()
	print(r)
else:
	#create the user on auth0

	payload = {"connection": "Username-Password-Authentication",
	  "email": args.remail,
	  "password": args.rpassword,
	  "user_metadata": {
		  "publicKeyExponent": publicExponent,
		  "publicKeyModulus": modulus,
		  "privateKeyModulus": modulus,
		  "privateKeyExponent": privateExponent
		},
	  "app_metadata": {}
	  }
	  
	createRequest = requests.post('https://enel500blockvote.auth0.com/api/v2/users', headers = Auth0Header,  json = payload)


	print(createRequest)
	r=createRequest.json()
	print(r)
#Create the user on Blockvote 
BlockvoteHeader = {"Authorization" : id_token,
	"AccessToken" : access_token}
	
payload = {"region":args.region,
	"registrarName":args.rname,
	"registrarKeyModulus": modulus,
	"registrarKeyExponent":publicExponent,
	"registrarDistrict":args.district}
	
initRequest = requests.post('https://blockvotenode2.mybluemix.net/addRegistrar', headers = BlockvoteHeader, data = payload)
print(initRequest)
r=initRequest.json()
print(r)