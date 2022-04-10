from __future__ import print_function

import os.path
import pickle
from typing import Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


generic_is_present_err = "Email present in group or temporary error occurred"
generic_cannot_remove_err = "Could not remove email from one or more groups or temporary error occurred"


def credentials() -> Credentials:
    SCOPES = ['https://www.googleapis.com/auth/admin.directory.group',
              'https://www.googleapis.com/auth/admin.directory.group.member']
    creds = None

    pickle_file = 'token.pickle'
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open(pickle_file, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def lts_donator(donator_email: str, service: Resource, error_str: str) -> str:
    flag = None
    body = {
        'email': donator_email,
        'role': 'MEMBER',
    }
    try:
        response = service.members().insert(
            groupKey='script-lts-viewers@frostscript.com', body=body).execute()
        if response['type'] != 'USER':
            flag = f"Group email {donator_email} provided, user email required"
        else:
            if response['status'] == 'ACTIVE':
                flag = f"Successfully added {donator_email} to group"
            else:
                flag = 'Temporary error occurred, retry later!'
    except HttpError:
        return error_str
    return flag


def normal_donator(donator_email: str, service: Resource, error_str: str) -> str:
    flag = None
    body = {
        'email': donator_email,
        'role': 'MEMBER',
    }
    try:
        response = service.members().insert(
            groupKey='script-viewers@frostscript.com', body=body).execute()
        if response['type'] != 'USER':
            flag = f"Group email {donator_email} provided, user email required"
        else:
            if response['status'] == 'ACTIVE':
                flag = f"Successfully added {donator_email} to group"
            else:
                flag = 'Temporary error occurred, retry later!'
    except HttpError:
        return error_str
    return flag


def add_to_group(donator_email: str, donation_amt: int) -> str:
    creds = credentials()
    service = build('admin', 'directory_v1', credentials=creds)
    if donation_amt >= 10:
        flag_1 = lts_donator(donator_email, service, generic_is_present_err)
        flag_2 = normal_donator(donator_email, service, generic_is_present_err)
    else:
        flag_1 = None
        flag_2 = normal_donator(donator_email, service, generic_is_present_err)

    if flag_1 is not None:
        if flag_1 == generic_is_present_err or flag_2 == generic_is_present_err:
            return generic_is_present_err
        else:
            return "Success"
    else:
        if flag_2 == generic_is_present_err:
            return generic_is_present_err
        else:
            return "Success"


def remove_from_group(donator_email: str, donator_type: str) -> str:
    creds = credentials()
    service = build('admin', 'directory_v1', credentials=creds)
    groups = ['script-viewers@frostscript.com']
    if donator_type == 'LTS':
        groups.append('script-lts-viewers@frostscript.com')
    elif donator_type == 'Staff':
        groups.append('script-core-curators@frostscript.com')

    flag = False
    for group in groups:
        try:
            service.members().delete(groupKey=group, memberKey=donator_email).execute()
        except HttpError:
            flag = True

    if flag:
        return generic_cannot_remove_err
    return 'Success'


def change_donator_email(old_email: str, new_email: str, donator_type: str, donator_has_hw_access: str, donator_has_curator_access: str) -> list:
    creds = credentials()
    return_msgs = []
    service = build('admin', 'directory_v1', credentials=creds)
    groups = ['script-viewers@frostscript.com']
    if donator_type == 'LTS':
        groups.append('script-lts-viewers@frostscript.com')
    elif donator_type == 'Staff':
        groups.append('script-core-curators@frostscript.com')

    if donator_has_hw_access == 'Yes':
        groups.append('script-hw-viewers@frostscript.com')

    if donator_has_curator_access == 'Yes':
        groups.append('script-curators@frostscript.com')

    # Removal of emails
    flag = False
    for group in groups:
        try:
            service.members().delete(groupKey=group, memberKey=old_email).execute()
        except HttpError:
            flag = True

    if flag:
        return_msgs.append(generic_cannot_remove_err)

    # Addition of emails
    flag = False
    body = {
        'email': new_email,
        'role': 'MEMBER',
    }
    for group in groups:
        try:
            response = service.members().insert(groupKey=group, body=body).execute()
            if response['type'] != 'USER':
                flag = True
                flag_msg = f"Group email {new_email} provided, user email required"
                try:
                    service.members().delete(groupKey=group, memberKey=new_email).execute()
                except HttpError:
                    pass
            else:
                if response['status'] == 'ACTIVE':
                    pass
                else:
                    flag = 'Temporary error occurred, retry later!'
        except HttpError:
            flag = True
            flag_msg = None

    if flag:
        if flag_msg is not None:
            return_msgs.append(flag_msg)
        else:
            return_msgs.append(generic_is_present_err)

    return return_msgs


def set_nsfw_access(donator_email: str) -> str:
    creds = credentials()
    service = build('admin', 'directory_v1', credentials=creds)
    flag = False
    group = 'script-hw-viewers@frostscript.com'
    body = {
        'email': donator_email,
        'role': 'MEMBER',
    }
    try:
        response = service.members().insert(groupKey=group, body=body).execute()
        if response['status'] == 'ACTIVE':
            pass
        else:
            flag = True
            flag_msg = 'Temporary error occurred, retry later!'
    except HttpError:
        flag = True
        flag_msg = generic_is_present_err

    if flag:
        return flag_msg
    return 'Success'


def set_lts_access(donator_email: str) -> str:
    creds = credentials()
    service = build('admin', 'directory_v1', credentials=creds)
    flag = False
    group = 'script-lts-viewers@frostscript.com'
    body = {
        'email': donator_email,
        'role': 'MEMBER',
    }
    try:
        response = service.members().insert(groupKey=group, body=body).execute()
        if response['status'] == 'ACTIVE':
            pass
        else:
            flag = True
            flag_msg = 'Temporary error occurred, retry later!'
    except HttpError:
        flag = True
        flag_msg = generic_is_present_err

    if flag:
        return flag_msg
    return 'Success'
