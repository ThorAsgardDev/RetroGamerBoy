
import requests
import urllib
import configparser
import json


class SheetsClient():

	def __init__(self, api_key, oauth_client_id, oauth_client_secret, sheet_id, tokens_filename):
		self.api_key = api_key
		self.oauth_client_id = oauth_client_id
		self.oauth_client_secret = oauth_client_secret
		self.sheet_id = sheet_id
		self.tokens_filename = tokens_filename
		
		config = configparser.ConfigParser()
		config.read(tokens_filename)
		
		self.access_token = config["TOKENS"]["ACCESS_TOKEN"]
		self.refresh_token = config["TOKENS"]["REFRESH_TOKEN"]
		
	def get_request(self, path, param):
		if not param:
			param = {}
		param["key"] = self.api_key
		url = "https://sheets.googleapis.com/v4/spreadsheets/" + urllib.parse.quote(self.sheet_id) + path + "?" + urllib.parse.urlencode(param, True)
		response = requests.get(url)
		if response.status_code != 200:
			print("BAD STATUS: ", response, response.content)
			return
		return response.json()
		
	def send_post_request(self, path, payload):
		headers = {
			"Authorization": "Bearer " + self.access_token,
		}
		url = "https://sheets.googleapis.com/v4/spreadsheets/" + urllib.parse.quote(self.sheet_id) + path
		response = requests.post(url, headers = headers, data = json.dumps(payload))
		return response
		
	def post_request(self, path, payload):
		response = self.send_post_request(path, payload)
		if response.status_code == 401:
			response_json = response.json()
			if "error" in response_json and "status" in response_json["error"] and response_json["error"]["status"] == "UNAUTHENTICATED":
				self.refresh_tokens()
				response = self.send_post_request(path, payload)
				
		if response.status_code != 200:
			print("BAD STATUS: ", response, response.content)
			return
		return response.json()
		
	def refresh_tokens(self):
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
		}
		param = {
			"client_id": self.oauth_client_id,
			"client_secret": self.oauth_client_secret,
			"refresh_token": self.refresh_token,
			"grant_type": "refresh_token",
		}
		url = "https://www.googleapis.com/oauth2/v4/token"
		data = urllib.parse.urlencode(param, True)
		
		response = requests.post(url, headers = headers, data = data)
		
		if response.status_code != 200:
			print("BAD STATUS: ", response, response.content)
			
		response = response.json()
		
		self.access_token = response["access_token"]
		
		config = configparser.ConfigParser()
		config["TOKENS"] = {
			"ACCESS_TOKEN": self.access_token,
			"REFRESH_TOKEN": self.refresh_token,
		}
		with open(self.tokens_filename, "w") as f:
			config.write(f)
		
	def get_values(self, ranges):
		param = {
			"ranges": ranges,
			"fields": "properties.title,sheets(properties,data.startColumn,data.startRow,data.rowData.values(formattedValue,userEnteredFormat))",
			# "includeGridData": True,
		}
		return self.get_request("", param)
		
	def set_values(self, ranges_values):
		payload = {
			"valueInputOption": "USER_ENTERED",
			"data": ranges_values,
		}
		
		self.post_request("/values:batchUpdate", payload)
		
	def get_sheets(self):
		return self.get_request("", None)
		