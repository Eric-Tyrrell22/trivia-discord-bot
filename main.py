#!/usr/bin/env python3
import os
import ssl
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN=os.getenv('DISCORD_TOKEN')
GUILD=os.getenv('DISCORD_GUILD')



class Question():
  def __init__(self, creator, target, question):
    self.creator = creator
    self.target = target
    self.question = question
    self.score = 0

  def __repr__(self):
    return f'The question was {self.question}\nThe correct answer was . . . {self.target}\nAnd was created by . . . {self.creator}'

class Player():
  def __init__(self, name):
    self.name = name
    self.score = 0
    self.questions = []
    self.answered = False;

  def __repr__(self):
    return f'{self.name} - {self.score}'

  def add_question(self, question):
    self.questions.append(question)

  def list_questions(self):
    print(self.questions)
    return [str(q) for q in self.questions]

  def pop_question(self):
    print(self.questions)
    random.shuffle(self.questions)
    return self.questions.pop()


class FriendJeopardy(discord.Client ):
  async def on_ready(self):
    self.players = dict()
    self.game_state = 'waiting'
    self.current_question = None
    self.state = ''

    self.error_messages = {
      "!guess": "I couldn't understand the format of your guess. The correct format is '!guess TARGET CREATOR'",
      "!add": "The correct format to add a question is !add TARGET QUESTION..."
    }

    self.commands = {'!list': self.list_questions, '!add': self.add_question, '!remove_question': self.remove_question, '!guess': self.guess, '!name': self.change_name }

    self.admin_commands = {'!begin': self.begin_game, '!start': self.start_game, '!continue': self.continue_game, '!list_players': self.list_players, "!admin_list": self.admin_list_questions}

    print(f'{client.user} has connected to Discord!')
    print(client.guilds)

  async def on_message(self,message):

    player = message.author
    admin = player.name == 'Cicer22' and player.id == 338814918893633538
    
    print(message.channel)

    if player.id == self.user.id:
      return

    if player.name not in self.players:
      print(f'updating players with {player.name}')
      self.players[player.name] = Player(player.name)
    else:
      cur_player = self.players[player.name]

    self.current_player = self.players[player.name]

    
    possible_command = message.content.split()[0]
    message.content = ' '.join(message.content.split()[1:])

    # continue when all players have answered


    if possible_command in self.commands.keys():
      if not isinstance(message.channel, discord.channel.DMChannel):
        print('not a dm')
        pass
      else:
        try:
          await self.commands[possible_command](message)
        except:
          await self.handle_error(possible_command, message)

    if admin and possible_command in self.admin_commands.keys():
      await self.admin_commands[possible_command](message)

  async def handle_error(self, error, message):
    await message.channel.send(self.error_messages[error])

  async def add_question(self, message):
    if self.state != 'questions':
      await message.channel.send('Can\'t currently add a question. has the game already started?')
      return
    q = Question(self.current_player.name, message.content.split()[0], ' '.join(message.content.split()[1:]))
    self.players[message.author.name].add_question(q)
    await message.channel.send('added!')
    await self.list_questions(message)

  async def remove_question(self, message):
    if self.state != 'questions':
      await message.channel.send('Can\'t currently remove question. has the game already started?')
      return
    player = self.players[message.author.name]
    player.pop_question()
    await self.list_questions(message)
    

  async def admin_list_questions(self, message):
    p = self.players.values() 
    qs = [player.questions for player in p]
    q = [q for q in qs]
    flat_list = [str(item) for sublist in q for item in sublist]
    await message.channel.send('\n'.join(flat_list)) 

  async def list_questions(self, message):
    questions = self.current_player.list_questions()
    await message.channel.send('\n'.join(questions))

  async def list_players(self, message=''):
    players = [str(player) for player in self.players.values()]
    await self.main_channel.send("\n".join(players))

  async def change_name(self, message):
    if self.state != 'questions':
      await message.channel.send('You cannot change your name after the game\s begun')
      return

    self.current_player.name = message.content
    await message.channel.send(f'Your new name is {self.current_player.name}')

  async def guess(self, message):
    if self.state != 'started':
      await message.channel.send('there isn\'t currently a question to guess on')
      return

    player = self.players[message.author.name]

    if player.answered:
      message.channel.send('you\'ve already guessed this round')
      return

    who = message.content.split()[0]
    creator = message.content.split()[1]

    await self.score_guess(who, creator)
    player.answered = True

    await message.channel.send('guess received')
    round_over = all([x.answered for x in self.players.values()])

    if round_over:
      print('round should end')
      await self.end_round()

  async def score_guess(self, who, creator):
    if self.current_question.target.lower() == who.lower(): 
      self.current_player.score += 1
    if self.current_question.creator.lower() == creator.lower():
      self.current_player.score += 1

    return 

  async def begin_game(self, message):
    print('beginning game')
    self.state = 'questions'
    self.main_channel = message.channel
    await message.channel.send('beginning game')
  
  async def start_game(self, message):
    print('starting game')
    self.state = 'started'
    await message.channel.send('starting game')
    await self.start_round()
  
  async def continue_game(self, message):
    print('continuing game')
    await message.channel.send('continuing game')

  async def start_round(self):
    print('starting round')
    await self.list_players()
    await self.get_next_question()
    await self.main_channel.send(f'Current question: {self.current_question.question}')

  async def end_round(self):
    print('ending round')
    for player in self.players.values():
      player.answered = False

    await self.send_answer()
    await self.list_players()

    if len([player for player in self.players.values() if len(player.questions) > 0]) > 0:
      await self.start_round()
    else:
      await self.end_game()
  
  async def end_game(self):
    print('ending game')
    await self.main_channel.send('Game is over. you may now return to your regularly scheduled program')

  async def send_answer(self):
    await self.main_channel.send(self.current_question)

  async def send_player_scores(self):
    await self.main_channel.send('testing player scores')

  async def get_next_question(self):
    players_with_questions_left = [player for player in self.players.values() if len(player.questions) > 0]
    self.current_question = random.choice(players_with_questions_left).pop_question()
    print(self.current_question)
  

client = FriendJeopardy()
# I guess there's some weirdness with ssl on mac
# fix is in Applications/Python3.X
# Click on Install Certificates.command to run the fix.
#print(ssl.get_default_verify_paths())

client.run(TOKEN)

