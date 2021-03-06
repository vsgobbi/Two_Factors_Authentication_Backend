import os
from flask import Flask, jsonify, request, abort, url_for, session
from authy.api import AuthyApiClient
from authy import AuthyApiException
from google.cloud import datastore


app = Flask(__name__)
app.config.from_object('config')
try:
    api = AuthyApiClient(app.config['AUTHY_API_KEY'])
    #makes the API store the phonenumber for verification
    app.secret_key = 'super-secret'
except:
    raise AuthyApiException

#Create google datastore credential with API KEY and store it here:
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'your-api-5d1b7cdd2258.json'

datastore_client = datastore.Client()
builtin_list = list
kind = '2FA'


def get_all():
    query = datastore_client.query(kind='2FA')
    fetched = list(query.fetch())
    return fetched


def get_verifieds():
    query = datastore_client.query(kind='2FA')
    query.add_filter('verified', '=', True)
    fetched = list(query.fetch())
    return fetched


def add_user(name, phonenumber):
    #key = datastore_client.key(kind, str(phonenumber[:6]))
    key = datastore_client.key(kind, int(phonenumber % 100000))
    user = datastore.Entity(key)
    #must cast to str in order to hash phonenumber with NoSQL Datastore
    user['phonenumber'] = str(phonenumber)
    user['name'] = name
    user.update({
        'verified': False,
    })
    datastore_client.put(user)
    #For testing purpose
    #print('Stored user: {}: {}'.format(user['name'], user['phonenumber']))
    return user


def insert_token(token, phonenumber):
    key = datastore_client.key(kind, int(phonenumber % 100000))
    user = datastore.Entity(key=key)
    user = datastore_client.get(key)
    user['token'] = token
    datastore_client.put(user)
    #For test purpose
    #print('Stored token: {}: {}'.format(user['token'], phonenumber))
    return user


def from_datastore():
    key = datastore_client.key(kind, 'user')
    user = datastore_client.get(key)
    return user


def list_users(limit=10, cursor=None):
    ds = datastore_client

    query = ds.query(kind='2FA', order=['name'])
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(from_datastore(), page)
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor


def make_public(verified):
    new_verified_user = {}
    for field in verified:
        if field == 'id':
            new_verified_user['uri'] = url_for('get', profile_id=verified['id'], _external=True)
        else:
            new_verified_user[field] = verified[field]
    return new_verified_user


@app.route('/')
def get():
    return jsonify({'2FA profiles': builtin_list(map(make_public, get_all()))})


@app.route('/api/verifieds', methods=['GET'])
def get_profile():
    return jsonify({'verifieds_profiles': builtin_list(map(make_public, get_verifieds()))})


@app.route('/api/verify/<int:verify_phone>', methods=['POST'])
def get_profiles(verify_phone):
    query = datastore_client.query(kind='2FA')
    query.add_filter('phonenumber', '=', str(verify_phone))
    fetched = list(query.fetch())
    print(fetched)
    if not fetched: 
        return jsonify({'verify': "phone not founded"}), 400
    return jsonify({'verify': fetched}), 200


@app.route('/api/login', methods=['POST'])
def create_profile():
    if not request.json or not 'phonenumber' in request.json or "" in request.json:
        return jsonify({'Error': 'phone number not found'}), 400
    user_data = {
        'name': request.json['name'],
        'phonenumber': request.json['phonenumber'],
    }
    key_id = int(user_data['phonenumber'])
    phonenumber = str(user_data['phonenumber'])
    if len(phonenumber) != 11:
        return jsonify({'Wrong number format': 'Please insert your 11 digits '
                                               'phone number with area code and number ex:1196249256'}), 400
    #key = datastore_client.key(kind, str(phonenumber[6:]))
    key = datastore_client.key(kind, int(key_id % 100000))
    user = datastore.Entity(key)
    #must cast to str in order to hash phonenumber with NoSQL Datastore
    user['phonenumber'] = str(phonenumber)
    user['name'] = user_data['name']
    user['verified'] = False
    datastore_client.put(user)

    country_code = u'55'
    phone_number = request.json.get("phonenumber")
    
    #store the phone number for further validation
    session['phone_number'] = phone_number
    session['country_code'] = country_code
    session['key_id'] = int(key_id % 100000)
    api.phones.verification_start(phone_number, country_code, via='sms')
    return jsonify({'verification': make_public(user)}), 201


@app.route('/api/validate', methods=['POST'])
def test_token():
    if not 'token' in request.json or '' in request.json:
        return jsonify({'Error': 'token not found'}), 400
    user_data = {
        'token': request.json['token']
    }

    if len(str(user_data['token'])) != 4:
        return jsonify({'Error': 'token must have 4 digits'}), 400
    phone_number = session.get('phone_number')
    country_code = session.get('country_code')
    key_id = session.get('key_id')
    if not phone_number or not key_id:
        return jsonify({'Error': 'insert phonenumber first'}), 400
    #key = datastore_client.key(kind, str(phone_number[6:]))
    key = datastore_client.key(kind, int(key_id % 100000))
    user = datastore_client.get(key)
    user['token'] = user_data['token']
    datastore_client.put(user)
    verification_code = user_data['token']
    verification = api.phones.verification_check(phone_number, country_code, verification_code)
    if verification.ok():
        user_data['token'] = request.json
        user['verified'] = True
        datastore_client.put(user)
        return jsonify({'verification': make_public(user)}), 201
    ver_errors = str(verification.errors())
    return jsonify({user['verified']: str(ver_errors[12:-2])}), 400


if __name__ == '__main__':
    app.run(debug=True)
