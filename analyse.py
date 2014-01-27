import matplotlib.pyplot as plt
import sys,os

sec  = [0] # initialise to 0 as at time = 0, score = 0 and makes plot look nice
score = [0]
hostname = ""

graphicfilename = os.path.splitext(sys.argv[1])[0] + '.png'

print graphicfilename
with open(sys.argv[1]) as f:

    for line in f:
        try:
            ln = line.split()
            print ln
            if len(ln) == 1:
                hostname = ln[0].rstrip()
            score.append(ln[1]) # in the case that we have 
                                # the hostname, this will fail
                                # with an IndexError
            sec.append(ln[0])
        except IndexError:
            continue

secs = map(int, sec)
scores = map(int,score)
print max(scores)
print hostname

fig = plt.figure()
ax = fig.add_subplot(111)

ax.set_ylim(0,max(scores)+1)
ax.set_ylabel("Score - Completed Lifts")

ax.set_xlim(0,max(secs)+1)
ax.set_xlabel("Time - Seconds")

plt.figtext(0.6,0.3,hostname,color='red',variant='small-caps')

plt.plot(secs,score)
plt.savefig(graphicfilename)

quit()
