#####################################

import pika
import sys
import datetime as dt
import time

import threading, Queue, sys, socket

from Tkinter import *


#def finish():
#			print 'Into finish'
#		
#			def cb():
#				print "Trying to close connetion"
#				if self.score_connection.is_open:
#					self.score_connection.close()
#	
#
#			if self.score_channel:
#				print "Calling basic_cancel"
#				self.score_channel.basic_cancel(None, self.tag)
#
#
#			print "Done!"


class Score_Receiver():

	def __init__(self, queue):
		self.queue = queue


		# Consume all messages from kbscores and save them to a temp file
		self.score_connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='localhost'))
		# self.score_connection.add_timeout(3, finish)

		self.score_channel = self.score_connection.channel()
		#self.score_channel.exchange_declare(exchange = 'kbscores', type = 'fanout')
		self.score_result = self.score_channel.queue_declare(
			queue='kbscores')
			
		self.tag = self.score_channel.basic_consume(
			self.callback,
			queue = 'kbscores',
			no_ack = True)


	def callback(ch, method, properties,body):
		print "[x] into save_scores"
		hostname = body.split('\n')[0]
		with open(hostname+'.txt',"w") as f:
			f.write(body)


	def run():
		self.score_channel.start_consuming()

class Kb_server(Frame):

	def __init__(self, root):

		Frame.__init__(self,root)


		self.root = root

		self.startButton = Button(self, 
					  text = "Start", 
					  command=self.start)

		self.startButton.pack(fill = BOTH, expand = YES)

		self.threeMinuteButton = Button(self,
					text = "3 Minutes",
					command = self.three_minute_flight)

		self.threeMinuteButton.pack(fill = BOTH, expand = YES)

		self.sixMinuteButton = Button(self,
					text = "6 Minutes",
					command = self.six_minute_flight)

		self.sixMinuteButton.pack(fill = BOTH, expand = YES)

		self.tenMinuteButton = Button(self,
					text="10 Minutes",
					command = self.ten_minute_flight)

		self.tenMinuteButton.pack(fill = BOTH, expand = YES)

		

		self.stopButton = Button(self, 
					 text = "Stop", 
					 command = self.stop)

		self.stopButton.pack(fill = BOTH, expand = YES)

		self.resetButton = Button(self,
					  text = "Reset", 
					  command = self.reset)

		self.resetButton.pack(fill = BOTH, expand = YES)

		# Set up the communication channel
		self.connection = pika.BlockingConnection(
			pika.ConnectionParameters('localhost'))
		self.channel = self.connection.channel()

		self.channel.exchange_declare(exchange = 'kbcommands',
					      type = 'fanout')

		self.score_queue = Queue.Queue()
		self.score_receiver = Score_Receiver(self.score_queue)

	def start(self, duration = None):


		now = time.time()

		start_time = now + 0.1 # approx 100ms in the future
		start_message = "START:%f" % start_time


		self.channel.basic_publish( exchange = 'kbcommands',
									routing_key = '',
									body = start_message)
		print "[x] - sent message %s" % start_message

		if duration != None:

			end_time = start_time + duration

			self.stop(end_time)




	def ten_minute_flight(self):
		self.start(600000)

	def six_minute_flight(self):
		self.start(360000)

	def three_minute_flight(self):
		self.start(180000)


	def stop(self, stop_time = None):	

		stop_message = "STOP"

		if stop_time != None:
			stop_message += (":%f") % stop_time

		self.channel.basic_publish( exchange = 'kbcommands',
									routing_key = '',
									body = stop_message)
		print "[x] - sent message %s" % stop_message


	def on_timeout(self):
		print "Hit timeout call!"
		self.score_connection.close()

	def reset(self):


		# Send reset message to all the clients
		reset_message = "RESET"

		self.channel.basic_publish( exchange = 'kbcommands',
					    routing_key = '',
					    body = reset_message)

		print "[x] - sent message %s" % reset_message

		

		

if __name__ == '__main__':

	root = Tk()

	root.minsize(200,200)

	s = Kb_server(root)
	s.bind('<Configure>')
	s.bind('<Expose>')
	s.pack(fill=BOTH, expand=YES)
	root.mainloop()
