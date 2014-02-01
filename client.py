from Tkinter import *
import tkFont

import pika

import math,time
import threading, Queue, sys, socket

import RPi.GPIO as GPIO

from datetime import datetime as dt
from datetime import timedelta as td

class CommandConsumer():

    def __init__(self, thd_queue):
        
        self.thread_queue = thd_queue

         # Now open the comm channel
        self.connection = pika.BlockingConnection(
#            pika.ConnectionParameters('localhost'))
            pika.ConnectionParameters('192.168.0.10'))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange = 'kbcommands', 
            type = 'fanout')

        self.result = self.channel.queue_declare(exclusive=True)
        self.queue_name = self.result.method.queue

        self.channel.queue_bind(
            exchange = 'kbcommands', 
            queue = self.queue_name) 

        self.channel.basic_consume(
            self.callback, 
            queue=self.queue_name, 
            no_ack=True)

        
    def listen(self):
        self.channel.start_consuming()

    def callback(self,ch, method, properties, body):

        print "[x] %r" % (body,)
        if "START" or "STOP" or "RESET" in body:
            print "Adding msg to queue"
            self.thread_queue.put(body)
        else:
            print "Message not understood!" 

    def close_connection(self,event):
        print "stopping_listening"
        self.channel.basic_cancel()
        print "stopping consuming"
        self.connection.close() 
        print "done"

class ScoreHandler():


    def __init__(self, thd_queue):
        
        self.score_queue = thd_queue

         # Now open the comm channel
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='kbscores')

        
    def run(self):
        
        while self.score_queue.qsize():
            try:
                print "Processing score queue"
                msg = self.score_queue.get()
                print msg
                self.channel.basic_publish(
                    exchange = '',
                    routing_key = 'kbscores',
                    body = (socket.gethostname()+'\n'+ msg))
                print "Published!"
            except Queue.Empty:
                pass

    def close_connection(self,event):
        print "stopping_listening"
        self.channel.basic_cancel()
        print "stopping consuming"
        self.connection.close()
        print "done"
       
            

class Counter(Frame):

    """ Count up, down and reset"""

    def __init__(self,root):
        
        Frame.__init__(self,root)

        self.root = root

        self.customFont = tkFont.Font(family="Courier", size=200,weight="bold")

        self.scoreFrame = Text(root,font=self.customFont,
                               height = 1, width = 5,
                               bg = "blue",fg = "red")
        self.scoreFrame.tag_configure("center",justify='center')
        self.scoreFrame.insert(1.0," 000 ")
        self.scoreFrame.tag_add("center",1.0,END)
        self.scoreFrame.pack(fill = BOTH, expand = YES)

    
        self.timeFrame = Text(root,font=self.customFont,
                              height = 1, width = 5, 
                              bg = "black", fg = "green")
        self.timeFrame.tag_configure("center",justify='center')
        self.timeFrame.insert(1.0,"00:00")
        self.scoreFrame.tag_add("center",1.0,END)
        self.timeFrame.pack(fill = BOTH,  expand = YES)


        # Software Buttons
        #self.incrementButton = Button(self, text = "Add", 
        #                              command = self.incrementCounter)
        #self.incrementButton.pack(fill = BOTH, expand = YES)

        #self.decrementButton = Button(self, text = "Subtract", 
        #                              command = self.decrementCounter)
        #self.decrementButton.pack(fill = BOTH, expand = YES)


        # Hardware Buttons
        # The hardware buttons
        self.debounce = 0.2
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(24,GPIO.IN)
        GPIO.setup(27,GPIO.IN)
        GPIO.add_event_detect(24,GPIO.BOTH,
                              callback=self.incrementCounter)
        GPIO.add_event_detect(27,GPIO.BOTH,
                              callback=self.decrementCounter)


        self.counter = 0
        self.score_list = []
        
        self.Stop = True
        self.Reset = False
        
        self.initialTime = 0
        self.seconds = 0 
        self.interstitial = 0

        self.last_increment = 0
        self.last_decrement = 0

        self.start_job = None
        self.pause_job = None

        self.command_queue = Queue.Queue()
        self.score_queue = Queue.Queue()

        self.cmd_handler = CommandConsumer(self.command_queue)
        self.command_thread = threading.Thread(target=self.cmd_handler.listen)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        self.score_handler = ScoreHandler(self.score_queue)
        self.score_thread = threading.Thread(target = self.score_handler.run)
        self.score_thread.daemon = True
        self.score_thread.start()

        self.processCommandQueue()

    def incrementCounter(self,cb=None):
        
         # Guard against button presses when stopped
        #if self.Stop == True or self.Reset == True:
        #    return
        
        if cb != None:
            print "Hardware Increment Button pushed!"

        now = time.time()
        if (now - self.last_increment) < self.debounce:
            return

        self.last_increment = now

        self.counter += 1
        self.scoreFrame.delete(1.0,END)
        self.scoreFrame.insert(1.2," %03d " % self.counter)
        self.scoreFrame.tag_add("center",1.0,END)
        self.score_list.append((self.seconds,self.counter))

    def decrementCounter(self):

        # Guard against button presses when stopped
        #if self.Stop == True or self.Reset == True:
        #    return

        if cb != None:
            print "Hardware Decrement Button pushed!"

        now = time.time()

        if ( now - self.last_decrement ) < self.debounce:
            return

        self.last_decrement = now

        self.counter -= 1
        self.scoreFrame.delete(1.0,END)
        self.scoreFrame.insert(1.3, " %03d " % self.counter)
        self.scoreFrame.tag_add("center",1.0,END)
        try:
            self.score_list.pop()
        except IndexError:
            pass


    def processCommandQueue(self):
        # print "Processing message queue"
        while self.command_queue.qsize():
            try:
                msg = self.command_queue.get(0)
                print msg
                if "START" in msg:
                    print "Start message"
                    self.start(msg)
                elif "STOP" in msg:
                    print "Stop message"
                    self.stop(msg)
                elif "RESET" in msg:
                    print "Reset message"
                    self.reset()
                else:
                    print "ERROR - DID NOT UNDERSTAND MESSAGE"
            except Queue.Empty:
                pass
            
        self.after(100,self.processCommandQueue)


    def updateTime(self):

        if self.Stop == True:
            return
        elif self.Reset == True:
            self.timeFrame.delete(1.0,END)
            self.timeFrame.insert(1.0, "00:00")
            self.timeFrame.tag_add("center",1.0,END)
            return
        else:
            # Allow any fractional second to be added to the time silently
            # Since we are working in whole seconds, the other alternative
            # is to allow fractions of a second to disappear
            # This is bad - in the worst case, it looks like we skip a second
            # at the start of the timing period, which scares people!
            self.seconds = int(math.floor(time.time() - self.initialTime)) + self.interstitial

            self.s = td(seconds = self.seconds)
            d = td(1,1,1) + self.s

            t_str = "%(minutes)02d:%(seconds)02d" % {"minutes" : int(d.seconds/60), "seconds" : d.seconds % 60}

            self.timeFrame.delete(1.0,END)
            self.timeFrame.insert(1.0,t_str)
            self.timeFrame.tag_add("center",1.0,END)
            self.after(50,self.updateTime)


    def start(self,start_time = -1):
        print "starting timer"
        print "starting at " + str(start_time)
        print "time now " + str(time.time())
        # Parse the start message
        if start_time != -1:
            start_time = float(start_time.split(":")[1])

        if self.stop == False:
            return
        else:
            
            self.Stop = False
            self.Reset = False        
            
            if start_time == -1:
                self.initialTime = time.time()
            else:
                while start_time > time.time():
                    time.sleep(0.01)
                self.initialTime = time.time()

            self.updateTime()


    def stop(self,stop_time = -1):

        print "stopping timer"
        print "stopping at " + str(stop_time)
        print "time now " + str(time.time())
        
        # Parse the start message
        if ":" in stop_time :
            stop_time = float(stop_time.split(":")[1])

        if stop_time != "STOP":
            # STOPPING HAS A BUG - NEEDS TO FIGURE OUT THE MESSAGE CORRECTLY!
            # CURRENTLY HAS NOW WAY OF CORRECTLY IDENTIFYING WHEN TO STOP (SEES 'STOP' WHEN SHOULD SEE NOTHING)
            now = time.time()
            self.pause_job = self.after( (int(stop_time) - int(now)) , self.pause)
        else:
            self.pause()

    def pause(self):

        self.Stop = True
        self.Reset = False
        self.interstitial = self.seconds

        
    def reset(self):

        if self.start_job is not None:
            self.after_cancel(self.start_job)
       
        if self.pause_job is not None:
            self.after_cancel(self.pause_job)

        self.Stop = False
        self.Reset = True

        self.updateTime()

        self.score_list.append((self.seconds,self.counter))
        # Report the scores
        #for x in self.score_list:
        #    print "At second {0} score was {1}".format(x[0],x[1])

        # Push to handler
        scr_str=""
        for ent in self.score_list:
            scr_str += (str(ent[0]) + " " + str(ent[1]) + '\n')
        
        self.score_queue.put(scr_str)
        self.score_handler.run()

        self.counter = 0
        self.score_list = []

        self.seconds = 0
        self.interstitial = 0

        self.scoreFrame.delete(1.0,END)
        self.scoreFrame.insert(1.0,"%03d" % self.counter)
        self.scoreFrame.tag_add("center",1.0,END)

        self.updateTime()
        self.Stop = True
        self.Reset = False


    def bind(self,event):
        pass
#        if event == '<Destroy>':
#            self.scoreFrame.bind(event,self.cmd_handler.close_connection)

        # if event == '<Configure>':
        # #    self.scoreFrame.bind(event,self.scoreFrame.resizeEvent)
        #     self.timeFrame.bind(event,self.timeFrame.resizeEvent)
        # elif event == '<Expose>':
        #  #   self.scoreFrame.bind(event,self.scoreFrame.refresh())
        #     self.timeFrame.bind(event,self.timeFrame.refresh())
    def close_connections(self):
        self.cmd_handler.close_connection()
        self.score_handler.close_connection()


def main():
    
    

    root = Tk()
    root.attributes('-fullscreen', True)    
    c = Counter(root)
    
    root.wm_protocol('WM_WINDOW_DESTROY',c.close_connections)
    c.bind('<Destroy>')
    c.pack(fill=BOTH, expand=YES)
    c.updateTime()
    root.mainloop()
    
if __name__ == "__main__":
    
    main()
        
