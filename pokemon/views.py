# render - renders a page on request.
# redirect - redirects the user to a pre-defined url.
# get_object_or_404 - fetches the specified query object from the database. returns a 404 http error page if the specified record doesn't exist.
from django.shortcuts import render, redirect, get_object_or_404
# HttpResponse - used to return a simple html response to the user upon request.
# Http404 - custom 404 error.
from django.http import HttpResponse, Http404
# Calling the models/tables of the database defined in models.py.
from .models import Pokemon, UserProfile, Question, Submit
#authenticate, login - support inbuilt functions for building the authentication and login system.
from django.contrib.auth import authenticate, login
from django.contrib import auth
# Calling the form structures defined in forms.py
from .forms import TeamForm, LoginForm
# IntegrityError - raised on a database consistency error
from django.db import IntegrityError
# Extending the user models
from django.contrib.auth.models import User
import json
# serializers are used to serialize data, here return in the json format
from django.core import serializers
# @login_required decorator is additional in-built django based security for authenticating users
from django.contrib.auth.decorators import login_required
# Calling the helper functions defined in contorls.py
from .controls import *

"""
up always represents a UserProfile object.
u always represents a User model object.
user always represents request.user or the user that generates a request.
Status : 0 => Error.
Status : 1 => Succesful Operation.
Status : 2 => Game Time is up.
"""

# Create your views here.
# a simple test function to check if the server is up and running.
def test(request):
	return HttpResponse('Is this working?')

# The first function to be called when the root url is requested.
# The navigatory function.
def index(request):
	# If a team is already not authenticated by the django admin, make them register for the game first.
	if not request.user.is_authenticated() :
		return redirect('/pokemon/register')
	else :
		up = UserProfile.objects.get(user = request.user)
		if up.submitted == 1 : # submitted == 1 implies that the time of the game is up and all the teams are forcefully logged out.
			resp = {
				'status' : 2,
				'error_message' : "Time's up"
			}
			return HttpResponse(json.dumps(resp), content_type = "application/json")
		if up.chosen == 0 : # If the team is authenticated, logged in but have not chosen their starting pokemon yet. Ask them to choose it first.
			#up.chosen = 1
			#up.save()
			print('not chosen')
			return redirect('/pokemon/choose')
		else : # If the team maybe logging in for more than once-th time, simply let them continue their game from where they left.
			print('chosen')
			return render(request, 'pokemon/main.html')

# This function is called when the registration form is filled and submit button is clicked.
# The click of the submit button wraps up all the information in a request and pings the url of this function.
def register(request):
	# If the user has already registered, redirect them to the navigatory function (index function).
	if request.user.is_authenticated() :
		return redirect('/pokemon/')
	else :# This is simple form handling
		# Taking in the inputs from the POST request generated by the form and populating the database with the information that comes alongwith it.
		if request.method == 'POST' :
			# Creating the form object.
			form = TeamForm(request.POST)
			# Checking the validity of the submitted form.
			if form.is_valid() :
				# Conversion of form object into a dictionary object.
				data = form.cleaned_data
				if not check_data(data): # check data is used to check the correct regex, defined in controls.py.
					error_message = 'Form fields are not correct.Regex error. Enter them properly.'
					resp = { 'status': 0 , 'message' : message }
					return HttpResponse(json.dumps(resp), content_type = "application/json")

				u = User()
				u.username = data['teamname']
				u.set_password(data['password'])

				try :
					u.save()
				except IntegrityError :# A record with the same primary key, here username, as requested exists.
					message = 'Username already exists'
					resp = { 'status': 0 , 'message' : 'Team name already registered' }
					return HttpResponse(json.dumps(resp), content_type = "application/json")

				up = UserProfile()
				up.user = u
				up.teamname = data['teamname']
				up.name1 = data['name1']
				up.name2 = data['name2']
				up.phone1 = data['phone1']
				up.phone2 = data['phone2']
				up.email1 = data['email1']
				up.email2 = data['email2']
				up.idno1 = data['idno1']
				up.idno2 = data['idno2']
				up.save()

				resp = { 'status': 1 ,'message': 'Successfully Registered', 'teamname' : up.teamname}
				return HttpResponse(json.dumps(resp), content_type = "application/json")
			else:
				message = 'Form fields are not correct. Enter them properly.'
				resp = { 'status': 0 , 'message' : message }
				return HttpResponse(json.dumps(resp), content_type = "application/json")

		else : # In case of a GET request.
			form = TeamForm()
			return render(request, 'pokemon/register.html', {'form' : form})

# Allows the user to login using the login form fields.
def login(request) :
	# Check if the user is already logged in.
	if request.user.is_authenticated() :
		return redirect('/pokemon/')

	# Check if the request is sending data via POST request only.
	if request.POST :
		form = LoginForm(request.POST)

		if form.is_valid() :# Check if the inputs are in the valid format.
			data = form.cleaned_data # Conversion of form object into a dictionary object.
			teamname = data['teamname']
			password = data['password']
			user = authenticate( username = teamname, password = password)
			try :
				up = UserProfile.objects.get(user = user)

				# Check if the game has ended or not.
				if up.submitted == 1 :
					resp = {
						'status' : 2,
						'error_message' : "Time's up"
					}
					return HttpResponse(json.dumps(resp), content_type = "application/json")

				# Check if the game has started yet or not.
				sub = Submit.objects.get(submit_name = "lol")
				if sub.submitted == 1 or up.submitted == 1: # Game has not been started yet. Call of controls.play_on() will do the job.
					resp={
						'status':0,
						'error_message': 'The Game has not started yet ! Stay tuned'
					}
					return HttpResponse(json.dumps(resp), content_type = 'application/json')
			except :
				# Check if the user has entered the password correctly.
				resp={
					'status':0,
					'error_message':'Username or password is incorrect'
				}
				return HttpResponse(json.dumps(resp), content_type = 'application/json')

			# Check if the user exists
			if user is not None :
				if user.is_active :# Check if the account is not disabled by the admin.
					auth.login(request, user)
					# Logging in the user.
					resp = {
						'status': 1,
						'message' : 'Successfully Logged In'
					}
					return HttpResponse(json.dumps(resp), content_type = 'application/json')
				else : # Raise the following message in case of an error
					resp = {
						'status': 0,
						'error_message' : 'Your account is not active, please contact the site admin.'
					}
					return HttpResponse(json.dumps(resp), content_type = 'application/json')

			else : # Raise the following message in case of an error
				resp = {
					'status': 0,
					'error_message' : "Your username and/or password were incorrect."
				}
				return HttpResponse(json.dumps(resp), content_type = 'application/json')
		else : # Raise the following message in case of an error
			resp = {
				'status': 0,
				'error_message' : "Your from credentials are not valid."
			}
			return HttpResponse(json.dumps(resp), content_type = 'application/json')

	else : # In case of a get request make a form object and use it to capture the data from the form fields.
		form = LoginForm()
		return render(request, 'pokemon/register.html', {'form':form})

# This is a function that is called by the frontend whenever it requires the user's data to be displayed
@login_required
def get_details(request) :
	user = request.user
	try :
		up = UserProfile.objects.get(user = user)
	except :
		raise Http404
	# still remaining status

	resp = {
		'status' : 1,
		'pokemon' : (up.pokemon.question_number%10),
		'teamname' : up.teamname,
		'attempted_questions' : up.attempted_questions,
		'correct_questions' : up.correct_questions,
		'xp' : up.xp,
		'evolution_state':up.evolution,
		'pokemoney' : up.pokemoney,
		'fainted' : up.fainted
	}
	return HttpResponse(json.dumps(resp), content_type = "application/json")

# Function that logs out a user when called.
@login_required
def logout(request) :
	auth.logout(request)
	# Redirecting to the login page after logging out.
	return redirect('/pokemon/login/')

# Question is fetched from the database and displayed.
@login_required
def display_question(request):
	user = request.user
	up = UserProfile.objects.get(user = user)

	# Check if the game has ended or not.
	if up.submitted == 1 :
		resp = {
			'status' : 2,
			'error_message' : "Time's up"
		}
		return HttpResponse(json.dumps(resp), content_type = "application/json")

	# Check if the data is recieved alongwith the request or not.
	if request.POST :
		if str(request.POST.get('no')).isdigit():
			number = int(request.POST.get('no'))
		else:
			raise Http404
	else:
		raise Http404

	try:
		question = Question.objects.get(number = number)
		pokemon = Pokemon.objects.get(question_number = number)
	except:
		raise Http404

	# Calculating the money to be deducted for entering any landmark. In other words deducting the entry fee.
	if question.difficulty_level == 1 :
		diff = 100
	else:
		diff = 200
	up.pokemoney -= diff
	trial = (int(number) - 1)
	aq = up.attempted_questions.split()
	cq = up.correct_questions.split()

	# Updating the information regarding the number of attempts for a particular function.
	if aq[trial] == 3 :
		resp = {
			'status' : 0,
			'error_message' : 'You cannot attempt this question anymore.'
		}
		return HttpResponse(json.dumps(resp), content_type = "application/json")
	elif cq[trial] == 1:
		resp = {
			'status' : 0,
			'error_message' : 'You cannot attempt this question anymore.'
		}
		return HttpResponse(json.dumps(resp), content_type = "application/json")

	aq[trial] = str(int(aq[trial])+1)
	up.attempted_questions = ' '.join(aq)
	resp = {
		'status': 1,
		'question' : str(question.content),
		'visited' : aq[trial],
		'amount_deducted' : lol,
		'poke_type_1' : up.pokemon.poke_type,
		'poke_type_2' : pokemon.poke_type
	}

	up.save()

	return HttpResponse(json.dumps(resp), content_type = "application/json")

# The validation function.
@login_required
def answer(request):

	if request.POST:
		
		number = int(request.POST.get('no')) # The question number is recieved alongwith the request
		answer = str(request.POST.get('answer')) # Same with the answer

		question = get_object_or_404(Question, number = number) # Check if the requested question exists.
		user = request.user
		try:
			up = UserProfile.objects.get(user = user)
		except:
			raise Http404('Are you even authentic??')

		# Check if the game has ended or not.
		if up.submitted == 1 :
			resp = {
				'status' : 2,
				'error_message' : "Time's up"
			}
			return HttpResponse(json.dumps(resp), content_type = "application/json")

		trial = (int(number) - 1)
		aq = up.correct_questions.split()
		cq = up.correct_questions.split()

		# Check if the number of maximum trials of a question are exhausted.
		if aq[trial] == 3 or cq[trial] == 1 :
			raise Http404('You cannot attempt this question any further. Do not try to cheat :)')

		GymPokemon = get_object_or_404(Pokemon, question_number = number)
		GPokeType = GymPokemon.poke_type
		PokeType = up.pokemon.poke_type

		# Calculating the money to be added to the user's wallet in case of a correct answer.
		if PokeType == '1':
			if GPokeType == '2':
				stat = 100
			elif GPokeType == '3':
				stat = -100
			else:
				stat = 0
		elif PokeType == '2':
			if GPokeType == '1':
				stat = -100
			elif GPokeType == '4':
				stat = 100
			else:
				stat = 0
		elif PokeType == '3':
			if GPokeType == '1':
				stat = 100
			elif GPokeType == '4':
				stat = -100
			else:
				stat = 0
		else:
			if GPokeType == '2':
				stat = -100
			elif GPokeType == '3':
				stat = 100
			else:
				stat = 0

		answer = answer.lower()

		# Checking if the answer is correct or not.
		if answer == question.answer:

			# Doing the needful (updating the information for the user and their pokemon).
			# If the answer is correct.
			trial = (int(number) - 1)
			aq = up.correct_questions.split()
			aq[trial] = str(int(aq[trial])+1)
			up.correct_questions = ' '.join(aq)

			cq = up.correct_questions.split()
			cq[trial] = '1'
			up.correct_questions = ' '.join(cq)

			if question.difficulty_level == 1:
				up.pokemoney += (500 + stat)
				up.xp += (500 + stat)
			else:
				up.pokemoney += 2*(500 + stat)
				up.xp += 2*(500 + stat)

			# For evolution of the user's pokemon
			if up.xp >= 8000:
				evoultion_state = 3
			elif up.xp >= 4000:
				evoultion_state = 2
			else :
				evoultion_state = 1


			if up.evolution == evoultion_state :
				evolved = 0
			else :
				evolved = 1
				up.evolution = evoultion_state

			if evolved == 1:
				if up.evolution == 2 :
					if up.pokemon.poke_type == 1 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Charmelion')
					elif up.pokemon.poke_type == 2 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Wartortle')
					elif up.pokemon.poke_type == 3 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Ivysaur')
					elif up.pokemon.poke_type == 4 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Pikachu')
				elif up.evolution == 3 :
					if up.pokemon.poke_type == 1 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Charizard')
					elif up.pokemon.poke_type == 2 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Blastoise')
					elif up.pokemon.poke_type == 3 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Venusaur')
					elif up.pokemon.poke_type == 4 :
						up.pokemon = Pokemon.objects.get(poke_name = 'Raichu')

			up.save()

			print(up.pokemon.poke_type,up.pokemon,up.pokemon.question_number)
			resp = {
				'status': 1,
				'xp' : up.xp,
				'pokemoney' : up.pokemoney,
				'fainted' : up.fainted,
				'visited' : aq[trial],
				'correct' : cq[trial],
				'evolved' : evolved,
				'evolution_state' : evoultion_state,
				'pokemon' : (up.pokemon.question_number%10)
			}

			return HttpResponse(json.dumps(resp), content_type = "application/json")

		else:
			up.fainted = 1
			up.save()

			resp = {
				'status': 0,
				'fainted' : up.fainted,
				'xp' : up.xp,
				'pokemoney' : up.pokemoney
			}
			return HttpResponse(json.dumps(resp), content_type = "application/json")

	else:
		resp = {
			'status' : 1
		}
		return HttpResponse(json.dumps(resp), content_type = "application/json")

# Rendering the rulebook page.
def show_rulebook(request):
	return render(request, 'pokemon/rulebook.html')

# The function where user chooses their pokemon.
@login_required
def choose(request):
	if request.POST:
		user = request.user
		up = UserProfile.objects.get(user=user)

		if up.submitted == 1 :
			resp = {
				'status' : 2,
				'error_message' : "Time's up"
			}
			return HttpResponse(json.dumps(resp), content_type = "application/json")

		if up.chosen == 1 :
			return render(request, 'pokemon/main.html')

		pokemon = request.POST.get('pokemon')
		up.pokemon = Pokemon.objects.get(poke_name = pokemon)
		up.chosen = 1
		up.save()

		resp = {
			'teamname' : up.teamname,
			'status' : 1
		}

		return HttpResponse(json.dumps(resp), content_type = 'application/json')

	else:
		return render(request, 'pokemon/select-pokemon.html')

# Function to revive the user's pokemon.
@login_required
def pokecenter(request):
	user = request.user
	up = UserProfile.objects.get(user=user)

	if up.submitted == 1 :
		resp = {
			'status' : 2,
			'error_message' : "Time's up"
		}
		return HttpResponse(json.dumps(resp), content_type = "application/json")

	if up.evolution == 1:
		amount_deducted = 300
	elif up.evolution == 2:
		amount_deducted = 200
	elif up.evolution == 3:
		amount_deducted = 100

	if request.POST:
		up.pokemoney -= amount_deducted
		up.fainted = 0
		up.save()

		resp = {
			'status' : 1,
			'amount_deducted' : amount_deducted,
			'pokemoney' : up.pokemoney,
			'fainted' : up.fainted,
			'xp' : up.xp
		}

		return HttpResponse(json.dumps(resp), content_type = "application/json")

	else :
		resp = {
			'amount_deducted' : amount_deducted
		}

		return HttpResponse(json.dumps(resp), content_type = "application/json")

# A custom function made in the hope of a multi-server interconnected game.
# This function sends the informtaion of each user to the sorter server alongwith the information of which server it came from.
def send_all(request):
	ups = UserProfile.objects.all()

	server_no = 2

	resp = {}
	players = []

	for up in ups :
		details = {
			'teamname' : up.teamname,
			'pokemoney' : up.pokemoney,
			'name1' : up.name1,
			'name2' : up.name2,
			'server' : server_no
		}

		players.append(details)

	resp['players'] = players

	return HttpResponse(json.dumps(resp), content_type = "application/json")


'''
def ajax(request):
    data = {}
    data['something'] = 'useful'
    return HttpResponse(json.dumps(data), content_type = "application/json")

This would work fine if you fill the data your self, but if you are getting the data from a model try the following:

def tasks_json(request):
    tasks = Task.objects.all()
    data = serializers.serialize("json", tasks)
    return HttpResponse(data, content_type='application/json')
'''
