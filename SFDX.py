#!/usr/bin/env python3.7
# encoding: utf-8
# https://github.com/mschmidtkorth/iTerm-salesforce-dx/tree/master
import iterm2

aliasOrUsername = ''


async def main(connection):
	# Executing 'sfdx force:org:display' takes >5 seconds, which would timeout coro() if executed within. Therefore, 'sfdx force:org:display' is only executed on demand within the onclick handler.
	@iterm2.RPC
	async def displayExpirationDate(session_id):
		await component.async_open_popover(session_id, "<p style='font-family: Arial'>Retrieving org expiration date... <em>(wait)</em></p>", iterm2.Size(300, 30))

		from subprocess import Popen, PIPE
		import json
		p = Popen(['sfdx force:org:display --targetusername=' + aliasOrUsername + ' --json'], stdin = PIPE, stdout = PIPE, stderr = PIPE, universal_newlines = True, shell = True)
		stdout, stderr = p.communicate()
		result = ''
		if stdout:
			result = json.loads(stdout)
		if stderr:
			result = json.loads(stderr)
		expiration = ''
		if stderr and 'status' in result and result['status'] == 1:
			expiration += '(error)'
		elif stdout and 'status' in result and (result['status'] == 'Active' or result['status'] == 0):
			expiration += result['result']['expirationDate']
		elif stdout and 'status' in result and (result['status'] == 'Expired' or result['status'] != 0):
			expiration += '(expired)'
		elif stdout:
			expiration += 'Never - org is a sandbox.'

		await component.async_open_popover(session_id, "<p style='font-family: Arial'>The scratch org expires on: <strong>" + expiration + '</strong></p>', iterm2.Size(350, 30))

	knobs = [iterm2.CheckboxKnob("Enable expiration date", False, "showExpirationDate")]
	component = iterm2.StatusBarComponent(short_description = "SFDX Status", detailed_description = "Provides status info for SFDX project folders", knobs = knobs, exemplar = u"\u2601 SFDC-1234 user@salesforce.com", update_cadence = None, identifier = "com.msk.sfdx")

	@iterm2.StatusBarRPC
	async def coro(knobs, path = iterm2.Reference("path"), cwd = iterm2.Reference("user.currentDir?")):
		import os
		import json
		from pathlib import Path

		currentDir = path
		if 'force-app' in currentDir: # User is in subdirectory
			currentDir = currentDir.split('force-app')[0] # Get root directory of project folder
		if Path(currentDir + '/sfdx-project.json').is_file(): # Current folder is sfdx folder
			# Retrieve defaultusername = alias
			dir = currentDir if Path(currentDir + '/.sfdx/sfdx-config.json').is_file() else os.environ['HOME'] # Get config from project folder if present, or global config
			with open(dir + '/.sfdx/sfdx-config.json') as configFile:
				config = json.load(configFile)
			global aliasOrUsername
			aliasOrUsername = config['defaultusername']

			# Retrieve username for alias
			with open(os.environ['HOME'] + '/.sfdx/alias.json') as aliasFile:
				alias = json.load(aliasFile)

			if 'defaultusername' in config and 'orgs' in alias:
				return u'\u2601 ' + config['defaultusername'] + u' \u2022 ' + alias['orgs'][config['defaultusername']]
			else:
				return u'\u2601' # Some error occurred, e.g. file not found or wrong content
		else:
			return u'\u2601' # No SFDX directory

	await component.async_register(connection, coro, timeout = 15.0, onclick = displayExpirationDate)


iterm2.run_forever(main)
