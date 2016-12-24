# pymessage

A sqlite powered simple messaging system built on Flask

## Installation

1. Install the app from the root of the project directory
* pip install --editable .

2. Instruct Flask to use the application
* export FLASK_APP=pymessage

3. Initialize the database
* flask initdb

5. Start the app
* flask run

## Usage

Add user that can receive messages:
POST http://localhost:5000/adduser/{username}

Send message to a user:
POST http://localhost:5000/{username}
Content-Type: application/json
Body: {"message": "The message to send"}

Get unread messages:
GET http://localhost:5000/{username}

Get messages based on index:
GET http://localhost:5000/{username}?from={from_idx}&to={to_idx}

Delete a message:
DELETE http://localhost:5000/{username}/{id}

Example using curl:

curl -X POST http://localhost:5000/testuser
curl -H "Content-Type: application/json" -X POST -d '{"message":"Test message to testuser"}' http://localhost:5000/testuser
curl -X GET http://localhost:5000/testuser
curl -X GET http://localhost:5000/testuser?from=0&to=10
curl -X DELETE http://localhost:5000/testuser/1

