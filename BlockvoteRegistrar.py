import argparse
import sys
import requests
import json
import base64
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
parser.add_argument("district", help="the registrar district")

args = parser.parse_args()

registrarInfoRequest = requests.get('https://blockvotenode2.mybluemix.net/getRegistrarInfo')

if args.rname in registrarInfoRequest.text:
	print("Registrar already in Blockvote Blockchain")
	sys.exit()

#Get API token
payload = {"grant_type":"client_credentials",
"client_id": "mjgRuEI10KlWWa7kAic7m6sD75FV0X81",
"client_secret": "gjNBs1NbFzX1xWw-zhBexGJpqZD-_hF0lK5Pg5H3yCSscx7bg-kZiLOJT3Ai5blt",
"audience": "https://enel500blockvote.auth0.com/api/v2/"
}

apiTokenRequest = requests.post("https://enel500blockvote.auth0.com/oauth/token", data = payload)
if apiTokenRequest.ok:
	print("Access Token Obtained")
else:
	print("Could not get Authentication token")
	print(apiTokenRequest.text)
	sys.exit()
r=apiTokenRequest.json()
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

if apiTokenRequest.ok:
	print("Logged in to Auth0")
else:
	print("Could not login to Auth0")
	print(loginRequest.text)
	sys.exit()
r=loginRequest.json()
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
userExists = True
if len(r)<>1:
	userExists= False


if userExists:
	print("User found on Auth0. Updating Information.")
	userID=r[0]["user_id"]
	payload = {
  "user_metadata": {
      "name":args.rname,
	  "publicKeyExponent": publicExponent,
	  "publicKeyModulus": modulus,
	  "privateKeyModulus": modulus,
	  "privateKeyExponent": privateExponent
	}
  }
  
	updateRequest = requests.patch('https://enel500blockvote.auth0.com/api/v2/users/'+userID, headers = Auth0Header,  json = payload)
	if updateRequest.ok:
		print("User updated on Auth0.")
	else:
		print("Could update user on Auth0")
		sys.exit()
else:
	#create the user on auth0
	print("User not found on Auth0. Creating new user.")
	payload = {"connection": "Username-Password-Authentication",
	  "username":args.rname,
	  "name":args.remail,
	  "email": args.remail,
	  "password": args.rpassword,
	  "user_metadata": {
	      "name":args.rname,
		  "publicKeyExponent": publicExponent,
		  "publicKeyModulus": modulus,
		  "privateKeyModulus": modulus,
		  "privateKeyExponent": privateExponent
		},
	  "app_metadata": {}
	  }
	  
	createRequest = requests.post('https://enel500blockvote.auth0.com/api/v2/users', headers = Auth0Header,  json = payload)
	if createRequest.ok:
		print("User Created on Auth0")
	else:
		print("Could not Create User")
		sys.exit()
#Create the user on Blockvote 
BlockvoteHeader = {"Authorization" : id_token,
	"AccessToken" : access_token}
	
payload = {"registrarName":args.rname,
	"registrarKeyModulus": modulus,
	"registrarKeyExponent":publicExponent,
	"registrarDistrict":args.district}
	
addRegistrarRequest = requests.post('https://blockvotenode2.mybluemix.net/addRegistrar', headers = BlockvoteHeader, data = payload)
print(addRegistrarRequest.json())
if addRegistrarRequest.ok:
	print("User registered with following information")
	print("Registrar Name: "+args.rname)
	print("District: "+args.district)
	print("Modulus: "+modulus)
	print("Public Exponent: "+publicExponent)
	print("Private Exponent: "+privateExponent)
else:
	print("Could not add registrar")