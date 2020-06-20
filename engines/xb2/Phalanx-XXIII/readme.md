## Additional Notes

The original readme document is in the file README.
This document contains some explanations on phalanx settings found on
[chess.com written by EscherehcsE][1].

> Summary: Phalanx XXIII isn't strong enough for cutting-edge analysis (2400+), but it's a nice engine to play against for fun.
> 
> Phalanx has been around for a while, but in the past I've had a hard time recommending it as a playing opponent. At the weak levels where I live, it moved instantly, and I found that a bit unnerving...So it never really made it to my short list. The engine's programmer, Dušan Dobeš, abandoned the project around 2000, so I figured we'd never see a new version. In 2006, Phalanx was resurrected by José de Paula Rodrigues and Jim Ablett (Phalanx Reborn), but it was mostly just the same old Phalanx.
> 
> Well, after a fourteen-year hiatus, Dušan's back...with a new version, Phalanx XXIII. And the new version no longer moves instantly at the low levels! Phalanx has a reputation for having an attractive playing style. According to Dušan, it's a "slow thinker" with lots of chess-specific knowledge.
> 
> Phalanx XXIII does have some quirks, but nothing I consider serious. It's only about a 2400+ elo engine, so if you're looking for a GM+ engine, look elsewhere.
> 
> It's a Winboard engine, so your GUI must be able to install Winboard engines. Also, most Winboard engines use configuration files for the engine settings, but Phalanx uses command-line switches instead of a configuration file. (Most GUIs have a place to enter engine command-line switches.)
> 
> The easy levels go from e1 to e99. The Phalanx README file states, "1 is the easiest and 99 is the hardest easy level". However, it's actually exactly the opposite; 99 is the easiest and 1 is the hardest easy level. I'm guessing that the e99 level is around 850 elo, and the e1 level is around 1600 elo.
> 
> You'll have to read through the README file to get familiar with the command-line switches, but it's not really that much work. On the line below are the command-line switches I use for the e1 level:
> -s+ -b- -e1
> 
> (The -s+ switch "shows thinking on", the -b- switch "turns opening book off" (I use the GUI book instead), and the -e1 switch "turns easy level 1 on". Also note that easy levels set hashtable size to zero, pondering and learning to off.)
> 
> As a second example, on the line below are the command-line switches I use for the full strength level:
> -s+ -t 131072 -b- -l-
> 
> (The -t 131072 switch sets the hash table size to 128 MB (131072 KB), and the -l- switch turns learning off.)
> 
> 
> Now, for the stronger players, you might have noticed that there are no easy levels between e1 and full strength (about 1600 - 2400 elo). What to do? Are you just out of luck? Luckily, Dušan has added two new switches in this version: the -n switch and the -z switch. These two new switches let you specify the nodes/second and a bit of randomness into the evaluation function. So, by adding these two new command-line switches, you can create an engine strength between e1 and full strength.
> 
> I created nine new engine strengths in this rating gap. Assuming that I normally set the Phalanx full-strength hashtable to 128 MB, and the full-strength nodes-per-second reach about 600,000 to 650,000 nps (my PC isn't that powerful), here are the command-line switches for those nine engines (You can simply copy-and-paste the switches into your GUI during engine installation):
> 
> [Edit on Nov 9, 2014 - I've found that these settings for Easy 0.9 through Easy 0.1 are very nonlinear; I'm working on finding settings that are more linear, but it will take some time.]
> 
```
Phalanx XXIII Easy 0.9 (about 1683 elo) :         -s+ -b- -l- -p- -n1000 -z 9 -t 256
Phalanx XXIII Easy 0.8 (about 1766 elo) :         -s+ -b- -l- -p- -n2000 -z 8 -t 512
Phalanx XXIII Easy 0.7 (about 1849 elo) :         -s+ -b- -l- -p- -n4000 -z 7 -t 1024
Phalanx XXIII Easy 0.6 (about 1932 elo) :         -s+ -b- -l- -p- -n8000 -z 6 -t 2048
Phalanx XXIII Easy 0.5 (about 2015 elo) :         -s+ -b- -l- -p- -n16000 -z 5 -t 4096
Phalanx XXIII Easy 0.4 (about 2098 elo) :         -s+ -b- -l- -p- -n32000 -z 4 -t 8192
Phalanx XXIII Easy 0.3 (about 2181 elo) :         -s+ -b- -l- -p- -n64000 -z 3 -t 16384
Phalanx XXIII Easy 0.2 (about 2264 elo) :         -s+ -b- -l- -p- -n128000 -z 2 -t 32768
Phalanx XXIII Easy 0.1 (about 2347 elo) :         -s+ -b- -l- -p- -n256000 -z 1 -t 65536
```
> 
> [Edit on Nov 9, 2014 - I've found that these settings for Easy 0.9 through Easy 0.1 are very nonlinear; I'm working on finding settings that are more linear, but it will take some time.]
> 
> (Note that the -p- switch sets pondering to off. Also, I don't know if the ratings for these nine settings are really linear, so the ratings are just a guesstimate.)

[//]: # (References) 
[1]: https://www.chess.com/forum/view/chess-equipment/phalanx-rebornand-we-really-mean-it-this-time-phalanx-xxiii
