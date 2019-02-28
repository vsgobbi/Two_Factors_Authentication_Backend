# Example of Two Factors Authentication API using Google Cloud App Engine and Google NoSQL Datastore

Note: When accessing API routers inside browser panel, use the following path: localhost:5000/api/{routes}.
In order to run it create a json file for google cloud credentials.
Please take a look how to create your App Engine project and export credentials:
https://flaviocopes.com/google-api-authentication/
You also can use 'curl' or 'httpie' instead of Postman to access the API.

### Installation
1. Create your own environment (virtualenv)
``` shell
        virtualenv -p python3.6 venv
        source venv/bin/activate
```
1.1 Check your python version and pip requirements:
``` shell
        python --version #should be 3.6 or greater
        pip install -r requirements.txt
```
2.0 Run your local server:
``` shell

        python main.py
```
2.1 Check your API-Root at localhost:5000

3.0 Check the postman.json file to test the API

3.1 Export pip libs to lib folder in order to deploy on google cloud:
``` shell
	pip install -t lib -r requirements.txt
```


3.2 Deploy to your App Engine:
``` shell
	gcloud app deploy
```


### GPL v.0.3
### Django RESTFUL API free to use under GPL license, created by vitorsgobbi@hotmail.com
