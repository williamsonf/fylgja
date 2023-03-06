Fylgja version 0.2.0
======
Fylgja is a Python-based platform that enables authenticated users to communicate with customized OpenAI models through a modular front-end.

---

Fylgja refers to a concept in Norse mythology and magic of a spirit or a creature that is closely linked to a particular individual or family. The Old Norse word "fylgja" means "to accompany" or "to follow".

According to Norse tradition fylgjas typically take the form of an animal or a human-like figure. They are said to follow their assigned person throughout their life, serving as a kind of guardian spirit or companion. The fylgja is believed to be intimately connected to the individual's fate or destiny and may even appear in prophetic dreams or visions.

Fylgjas are closely associated with the practice of seidr, a form of magic in which practitioners would enter into a trance-like state to gain insight into the past, present, and future. In seidr, the fylgja was often seen as a source of power and insight, and it was believed that a skilled seer could communicate with their fylgja to gain guidance and knowledge.

Today, the concept of the fylgja remains an important part of modern Nordic and Heathen traditions, where it is often seen as a representation of the personal or ancestral spirit that accompanies an individual throughout their life.

This concept serves as the primary inspiration behind the Fylgja platform: A virtual assistant who is capable of following the user from one means of communication to the next, whether that be a popular chat application, a website, email or something else. If the platform in question is not already supported, then it is intended that it is easy enough to add to Fylgja's repertoire.

Installation
------------
Deployment of Fylgja is a simple process and at this time requires very little set up.
A .env file is required to handle a number of variables, as follows:
* SYSTEM_PROMPT - a  prompt which will be provided to the bot each time, regardless of user. "You are a helpful assistant."
* CSV_WHITELIST - a filepath to a whitelist. An example .csv file has been included with this repository, in /authenticators
* CHATLOGS - a path to the folder where you want chatlogs to be stored
* MODEL - the model employed by open ai's chat completion endpoint. At the time of writing, this means
* OPENAI_ORG - your organization number for Open AI
* OPENAI_API_KEY - the api key for accessing Open AI's API
* DISCORD_API_KEY - the api key for deploying the discord bot

Beyond this, one need only run main.py

Contact Information
--------------------
Any questions or concerns regarding Fylgja should be directed to Fred Williamson.
He can be reached at williamson.f93@gmail.com

Versioning
-----------
Fylgja uses SemVer for its versioning  
In the following example x.y.z:  
  
* X will be incremented for incompatible changes that break backward compatibility with previous versions.
* Y will be incremented when adding new features or functionality in a backward-compatible manner.
* Z will be incremented when making backward-compatible bug fixes or small updates.

---

>"To call up a demon you must learn its name. Men dreamed that, once, but now it is real in another way. You know that, Case. Your business is to learn the names of programs, the long formal names, names the owners seek to conceal. True names..."  
>William Gibson, Neuromancer