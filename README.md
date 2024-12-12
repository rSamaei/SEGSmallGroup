# Team Cobra Small Group project

## Team members
The members of the team are:
- Mohammed Shafayat Hossain
- Muhammad Mushtaq Ahmad
- Endrin Hoti
- Adnan Hussain
- Reza Samaei

## Project structure
The project is called `code404`.  It currently consists of a single app `tutorials`.
Details on how to see and test functinality is provided at the bottom of this README file

## Deployed version of the application
The deployed version of the application can be found at [*(https://rsamaei.pythonanywhere.com/)*](*[https://rsamaei.pythonanywhere.com/*]).

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

To test functionality:

User @charlie is seeded with a matched session which will appear in calendar. @janedoe is matched with @charlie on this subject, and will show the same sessions on her calendar, furthermore @janedoe can approve of a session requested from @charlie, which will then allow both to see them on the calendar if accepted, leading on from this, @charlie can now provide the bank transfer number for the invoice on this session. Otherwise, to create own data all pages work as intended and can be used to create and view sessions, or match them as an admin


## Sources
The packages used by this application are specified in `requirements.txt`

Reza Samaei Sources Used:
Vector image (programming.svg) on home page was from www.svgrepo.com
