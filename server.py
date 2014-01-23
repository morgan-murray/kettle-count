#####################################

import pika
import sys
import datetime as dt
import time

from Tkinter import *


class Kb_server(Frame):

	def __init__(self, root):

		Frame.__init__(self,root)


		self.root = root

		self.startButton = Button(self, 
					  text = "Start", 
					  command=self.start)

		self.startButton.pack(fill = BOTH, expand = YES)

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

	def start(self):

		now = time.time()

		start_time = now + 0.1 # approx 100ms in the future
		start_message = "START:%f" % start_time


		self.channel.basic_publish( exchange = 'kbcommands',
									routing_key = '',
									body = start_message)
		print "[x] - sent message %s" % start_message
		#self.root.after(500,self.start)

	def stop(self):	

		stop_message = "STOP"

		self.channel.basic_publish( exchange = 'kbcommands',
									routing_key = '',
									body = stop_message)
		print "[x] - sent message %s" % stop_message


	def on_timeout(self):
		print "Hit timeout call!"
		self.score_connection.close()

	def reset(self):

		def callback(ch, method, properties,body):
			print "[x] into save_scores"
			hostname = body.split('\n')[0]
			with open(hostname+'.txt',"w") as f:
				f.write(body)

			def finish():
				print 'Into finish'
				ch.basic_cancel()
				ch.close()
				print "Done!"

			#number_msgs = pika.queue_declare(
#				'kbscores',passive=True)
			#print number_msgs

#			if number_messages == 0:
#				finish()
		# Send reset message to all the clients
		reset_message = "RESET"

		self.channel.basic_publish( exchange = 'kbcommands',
					    routing_key = '',
					    body = reset_message)

		print "[x] - sent message %s" % reset_message

		# Consume all messages from kbscores and save them to a temp file
		self.score_connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='localhost'))
		self.score_connection.add_timeout(5, self.on_timeout)

		self.score_channel = self.score_connection.channel()
		#self.score_channel.exchange_declare(exchange = 'kbscores', type = 'fanout')
		self.score_result = self.score_channel.queue_declare(
			queue='kbscores')
			
		self.score_channel.basic_consume(
			callback,
			queue = 'kbscores',
			no_ack = True)

		self.score_channel.start_consuming()

		

if __name__ == '__main__':

	root = Tk()

	root.minsize(200,200)

	s = Kb_server(root)
	s.bind('<Configure>')
	s.bind('<Expose>')
	s.pack(fill=BOTH, expand=YES)
	root.mainloop()
