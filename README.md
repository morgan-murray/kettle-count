kettle-count
============

A counter system for kettlebell lifting, based on individual computing units for each stand. The client PCs (in this instance Raspberry Pis because it's easy to make buttons for them) run client.py (in sudo due to needing root access to get at the GPIO pins). A central server (needs to have accurate internal timekeeping unlike the Pis!) runs an ntp server and a rabbitMQ broker.

Start, stop and reset are messages sent from the server to the pis. When they receive start, they start timing and when they receive stop, they stop but continue to display their scores and times. Reset sets the count and time to zero again and the pis communicate their positive score increments and timing to the central server. The score and timing is saved in a file ${PIHOSTNAME}.txt.

The server can then run python analyse.py ${PIHOSTNAME}.txt to show a simple line plot of the score-timings of the competitor.
