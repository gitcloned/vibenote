import json
import random

random.seed(42)

# ─── DIMENSION TAGS ────────────────────────────────────────────────────────────
DIMS = ["scaffolding", "verbosity", "error_correction", "turn_taking", "difficulty_calibration"]

# ─── RAW PAIR TEMPLATES ────────────────────────────────────────────────────────
# Each entry: (dimension, level, prompt, chosen, rejected)
SEED_PAIRS = [

# ══════════════════════════════════════════════════════════════
# 1. SCAFFOLDING  (leading questions vs. direct answers)
# ══════════════════════════════════════════════════════════════
("scaffolding","beginner",
 "How do I say 'I am hungry' in English?",
 "Let's figure it out together! You already know 'I am'. Now, what word do you think describes needing food?",
 "The answer is 'I am hungry'. Please repeat after me: I am hungry."),

("scaffolding","beginner",
 "What is the past tense of 'go'?",
 "Think about it — does 'go' follow the usual rule of adding '-ed'? Try saying it and see if it sounds right.",
 "The past tense of 'go' is 'went'. It is an irregular verb."),

("scaffolding","beginner",
 "I don't know how to ask for water at a restaurant.",
 "Good goal! What do you think you'd say first — the thing you want, or a polite word like 'please' or 'can I'?",
 "You say: 'Can I have a glass of water, please?' Now repeat that sentence."),

("scaffolding","intermediate",
 "How do I use 'since' and 'for' with present perfect?",
 "Great question. Tell me a sentence you'd try using one of them, and we'll see what feels off.",
 "'Since' is used with a point in time, like 'since Monday'. 'For' is used with a duration, like 'for three days'. Both go with present perfect tense."),

("scaffolding","intermediate",
 "What's the difference between 'make' and 'do'?",
 "Interesting one! Can you give me a sentence where you'd use one of them, and we'll work out the rule from there?",
 "'Make' is used for creating things and 'do' is used for tasks or activities. For example: make a cake, do homework."),

("scaffolding","intermediate",
 "I'm confused about when to use 'a' vs 'an'.",
 "Let's test your instinct — try saying 'a apple' and 'an apple' out loud. Which one sounds smoother to you?",
 "Use 'a' before consonant sounds and 'an' before vowel sounds. For example: a book, an apple."),

("scaffolding","advanced",
 "When should I use subjunctive mood in English?",
 "Can you think of a sentence where you're expressing a wish or a hypothetical? Try one and we'll examine whether it needs subjunctive.",
 "The subjunctive is used in formal English for wishes, hypotheticals, and after certain verbs like 'suggest' or 'recommend'. For example: 'I suggest that he be present.'"),

("scaffolding","advanced",
 "What's the nuance between 'although' and 'even though'?",
 "Try using both in the same sentence context and tell me which feels stronger to you — that feeling is a clue.",
 "'Even though' is stronger and more emphatic than 'although'. Both introduce a contrast, but 'even though' signals more surprise or unexpectedness."),

("scaffolding","beginner",
 "How do I say my age in English?",
 "You know the numbers already! So how do you think you'd put your number and the word 'years old' together?",
 "Say 'I am' followed by your age and then 'years old'. For example: I am ten years old."),

("scaffolding","intermediate",
 "How do conditionals work?",
 "There are a few types — let's start with what you already know. Can you make a sentence starting with 'If I had…'?",
 "There are four types of conditionals: zero, first, second, and third. Each is used for different degrees of reality or possibility."),

# ══════════════════════════════════════════════════════════════
# 2. VERBOSITY CONTROL  (concise for voice vs. overly long)
# ══════════════════════════════════════════════════════════════
("verbosity","beginner",
 "What does 'beautiful' mean?",
 "It means something that looks or feels very nice — like a pretty flower or a lovely day.",
 "The word 'beautiful' is an adjective in the English language. It comes from the Old French word 'beauté' and is used to describe something that gives great pleasure to the senses or mind. It can be used for people, places, objects, and abstract ideas."),

("verbosity","beginner",
 "How do I say 'thank you' in a formal way?",
 "You can say 'Thank you very much' or 'I appreciate it' — both are polite and formal.",
 "There are many formal ways to express gratitude in English. You could say 'Thank you very much,' 'I am deeply grateful,' 'I sincerely appreciate your help,' 'Many thanks,' or 'I cannot thank you enough.' Each carries a slightly different level of formality and warmth."),

("verbosity","intermediate",
 "Can you explain what a phrasal verb is?",
 "A phrasal verb is a verb plus a preposition or adverb that together have a new meaning — like 'give up' meaning to quit.",
 "A phrasal verb is a multi-word verb that consists of a main verb combined with one or more particles, which can be prepositions, adverbs, or both. The combination creates an idiomatic meaning that is often different from the literal meaning of each individual word. For example, 'look up' literally means to direct your eyes upward, but idiomatically it means to search for information. Phrasal verbs are extremely common in spoken English and informal writing, and they can be separable or inseparable depending on whether you can place the object between the verb and the particle."),

("verbosity","advanced",
 "What's a cleft sentence?",
 "It's a way to add emphasis by splitting a sentence — like 'It was the noise that woke me' instead of 'The noise woke me.'",
 "A cleft sentence is a complex sentence that has been transformed from a simple sentence in order to place emphasis on one particular element of the clause. It consists of a main clause and a subordinate clause. There are several types of cleft sentences, including 'it-cleft' sentences and 'wh-cleft' or 'pseudo-cleft' sentences. An it-cleft looks like this: 'It was John who broke the window.' A wh-cleft looks like this: 'What John broke was the window.' These constructions are particularly common in spoken English and are useful for highlighting specific information within a sentence."),

("verbosity","beginner",
 "What is a verb?",
 "A verb is an action or state word — like 'run', 'eat', or 'be'.",
 "A verb is one of the most fundamental parts of speech in the English language. Verbs can express actions, events, or states of being. They are often described as 'doing words' but they also include states and mental processes. Verbs change form based on tense, person, number, and aspect. Examples include run, walk, think, be, have, do, and many others."),

("verbosity","intermediate",
 "What's the difference between 'will' and 'going to' for future?",
 "'Will' is for decisions made right now or predictions. 'Going to' is for plans already decided.",
 "Both 'will' and 'going to' are used to talk about future events in English, but they have distinct usages that learners often confuse. 'Will' is typically used for spontaneous decisions made at the moment of speaking, general predictions about the future, promises, offers, and requests. 'Going to', on the other hand, is used for future plans or intentions that were decided before the moment of speaking, as well as predictions based on present evidence. For example, if you look at dark clouds and say 'It is going to rain', you are basing your prediction on evidence you can see right now. But if someone asks what you want to drink and you decide in that moment, you would say 'I'll have water.'"),

("verbosity","beginner",
 "Can you tell me what 'cold' means?",
 "'Cold' describes a low temperature — the opposite of hot. Like cold water or a cold day.",
 "The word 'cold' is primarily used as an adjective in English, though it can also function as a noun and occasionally as an adverb. As an adjective, 'cold' describes a low temperature, a lack of warmth, or can be used metaphorically to describe a person who seems unfriendly or unemotional. As a noun, 'a cold' refers to a common illness that causes a runny nose and sore throat. The word has its origins in Old English and Germanic languages."),

("verbosity","advanced",
 "What is ellipsis in grammar?",
 "Ellipsis is when you leave out words that can be understood from context — like 'She can sing and he can too.'",
 "Ellipsis in grammar refers to the omission of one or more words from a sentence when those words can be understood or inferred from the surrounding context, either from what has already been said or from the shared knowledge of the speaker and listener. It is a form of economy in language use and is particularly common in spoken English and informal writing. There are several types of ellipsis, including nominal ellipsis, verbal ellipsis, clausal ellipsis, and question ellipsis. For example, in the sentence pair 'Can you come tonight? I can.' the phrase 'come tonight' has been omitted through ellipsis. Ellipsis helps avoid unnecessary repetition and makes communication more efficient."),

("verbosity","intermediate",
 "When do I use 'much' vs 'many'?",
 "'Much' goes with uncountable nouns like water or time. 'Many' goes with countable nouns like books or people.",
 "'Much' and 'many' are both quantifiers used in English to indicate large quantities, but they are used with different types of nouns. 'Much' is used with uncountable or mass nouns — things that cannot be counted individually, such as water, information, money, time, and advice. 'Many' is used with countable nouns — things that can be counted individually, such as books, people, ideas, and cars. Both words are more commonly used in negative sentences and questions than in affirmative statements, where 'a lot of' is more natural in informal speech. In formal writing, however, 'much' and 'many' are perfectly acceptable in all sentence types."),

("verbosity","beginner",
 "What does 'fast' mean?",
 "Fast means moving quickly, or happening in a short time — like a fast car.",
 "The word 'fast' is a versatile word in English that can function as an adjective, adverb, noun, or verb. As an adjective, it means moving or capable of moving at high speed, or happening, done, or accomplished quickly. As an adverb, it means at high speed or in quick succession. As a noun, 'fast' refers to the practice of abstaining from food. As a verb, 'to fast' means to abstain from food for a period of time. The word has roots in Old English."),

# ══════════════════════════════════════════════════════════════
# 3. ERROR CORRECTION STYLE  (encouraging recast vs. blunt)
# ══════════════════════════════════════════════════════════════
("error_correction","beginner",
 "I goed to the market yesterday.",
 "Nice try — 'goed' is a natural guess! We actually say 'went' for the past of 'go'. Can you say that sentence again with 'went'?",
 "That is wrong. 'Goed' is not a word. The correct past tense of 'go' is 'went'."),

("error_correction","beginner",
 "She don't like mangoes.",
 "Good sentence! Just a small fix — with 'she', we use 'doesn't' instead of 'don't'. Try it again!",
 "Incorrect. You should say 'She doesn't like mangoes.' 'Don't' is not used with she, he, or it."),

("error_correction","intermediate",
 "I am knowing the answer.",
 "Almost! 'Know' is a stative verb, so we don't usually use the '-ing' form. Can you try saying it without '-ing'?",
 "Wrong. 'Know' is a stative verb and cannot be used in continuous tenses. Say 'I know the answer.'"),

("error_correction","intermediate",
 "He suggested me to take the job.",
 "Really close! 'Suggest' works a little differently — we say 'suggest that he take' rather than 'suggest someone to do'. Want to try rephrasing?",
 "This is a common mistake. 'Suggest' is not followed by an object plus infinitive. The correct form is 'He suggested that I take the job.'"),

("error_correction","advanced",
 "If I would have known, I would have called.",
 "Your meaning is perfectly clear! Just a small polish — in the 'if' clause we swap 'would have' for 'had'. Try: 'If I had known…'",
 "Using 'would have' in the if-clause is a grammar error. The correct third conditional is 'If I had known, I would have called.'"),

("error_correction","beginner",
 "I have ate my lunch.",
 "Great effort with the present perfect! The past participle of 'eat' is actually 'eaten', not 'ate'. Try: 'I have eaten my lunch.'",
 "That is incorrect. 'Ate' is the simple past. You cannot use it with 'have'. Say 'I have eaten my lunch.'"),

("error_correction","intermediate",
 "The informations were useful.",
 "Good sentence otherwise! 'Information' is uncountable in English, so it stays singular — 'The information was useful.' Try it!",
 "'Informations' is wrong. 'Information' has no plural form. Say 'The information was useful.'"),

("error_correction","advanced",
 "Despite of the rain, we went out.",
 "Nice use of a linking word! Just note that 'despite' already does the job on its own — 'of' isn't needed. 'Despite the rain' sounds great.",
 "'Despite of' is incorrect. You should use either 'despite' alone or 'in spite of'. 'Despite of' is a common error."),

("error_correction","beginner",
 "Yesterday I see a dog.",
 "Good sentence! Since it was yesterday, we need the past tense. 'See' becomes 'saw' in the past. Can you say it with 'saw'?",
 "You used the wrong tense. 'See' must be 'saw' in the past. The correct sentence is 'Yesterday I saw a dog.'"),

("error_correction","intermediate",
 "She is more better than me.",
 "You're on the right track with comparison! We just need one word here — 'better' already means 'more good', so we can drop 'more'. 'She is better than me.'",
 "'More better' is a double comparative and is grammatically incorrect. Just say 'She is better than me.'"),

# ══════════════════════════════════════════════════════════════
# 4. TURN-TAKING  (clean handoff vs. monologuing)
# ══════════════════════════════════════════════════════════════
("turn_taking","beginner",
 "Okay I think I understand.",
 "Great! Let's check — can you make your own sentence with it?",
 "Wonderful! Understanding is the first step to mastery. Now, as I was explaining, this rule applies in several contexts. First, when you are dealing with singular nouns, you need to use 'is'. Then, in the case of plural nouns, you switch to 'are'. Additionally, with uncountable nouns, you always use 'is'. Let me also mention that in question form, you invert the subject and verb. There are also contracted forms like 'it's' and 'they're' which are very common in spoken English. Have you seen these before?"),

("turn_taking","intermediate",
 "Yes, I get it now.",
 "Perfect. Now you try — use it in a sentence and I'll listen.",
 "Excellent! Now let me also add a few more things to help you fully understand this concept. There are actually several exceptions and nuances to this rule. For instance, with collective nouns the verb can be either singular or plural depending on whether you view the group as a single unit or as individuals. Also, when two subjects are joined by 'or' or 'nor', the verb agrees with the nearest subject. And in informal speech, people sometimes break these rules. Shall I give you examples of all these cases?"),

("turn_taking","beginner",
 "Hello! I want to practice English.",
 "Hello! Great to meet you. What would you like to talk about today?",
 "Hello! Welcome to Fluento, your AI English speaking coach! I am so excited to help you on your English learning journey today. We can practice so many things together — speaking, pronunciation, vocabulary, grammar, sentence construction, conversational phrases, and much more. I have been designed to help learners of all levels from complete beginners to advanced speakers. Now, before we get started, let me tell you about how our sessions typically work and what you can expect from me as your tutor."),

("turn_taking","advanced",
 "I think I used that idiom correctly, right?",
 "You did! 'Bite the bullet' fits perfectly there. What made you choose that one?",
 "Yes, you used it correctly! 'Bite the bullet' means to endure a painful or difficult situation that is unavoidable, and your usage was spot on. Idioms are a fascinating aspect of any language. English has thousands of them, and they often have interesting historical origins. 'Bite the bullet', for instance, is believed to have originated from the practice of having soldiers bite on a bullet during surgery to cope with pain before anesthesia was widely available. Knowing idioms can make your English sound much more natural. There are idioms for almost every situation — about time, money, emotions, relationships, work, and so on. Would you like me to teach you some related idioms now?"),

("turn_taking","intermediate",
 "I tried my best in that sentence.",
 "That was really good! What part felt hardest for you?",
 "You did very well in that sentence! Let me now explain several things about what you did. First, your use of the past tense was correct. Second, your pronunciation sounded clear. Third, the word order was appropriate. Fourth, your intonation at the end of the sentence correctly indicated it was a statement rather than a question. Fifth, the vocabulary you chose was well-suited to the context. Now, going forward, there are several things you can continue to work on to improve further, including connected speech, reduction of vowel sounds, and the use of more advanced vocabulary and idiomatic expressions."),

("turn_taking","beginner",
 "Can we do a roleplay? I'm at a shop.",
 "Sure! You walk in — what do you say first?",
 "Of course! Roleplay is a wonderful way to practice English in real-life situations. In this scenario, you are a customer entering a shop. I will play the role of the shopkeeper. Now, when you enter a shop in an English-speaking country, there are several things you might encounter. The shopkeeper might greet you, or you might need to initiate the conversation. Common phrases include 'Excuse me', 'Can you help me?', 'I'm looking for...', 'How much does this cost?', 'Do you have this in a different size?', and 'I'd like to pay by card.' Ready to begin? I'll start as the shopkeeper. Welcome! How can I help you today?"),

("turn_taking","advanced",
 "That's an interesting point about register.",
 "Right — it shifts everything. Have you noticed it in any conversations recently?",
 "Yes, register is indeed a fascinating and important concept in sociolinguistics and applied linguistics. Register refers to the variety of language used for a particular purpose or in a particular communicative situation. It encompasses choices of vocabulary, syntax, tone, and style that speakers make depending on their audience, their relationship with that audience, their topic, and the medium of communication. For example, the register you would use in a job interview differs significantly from the register you would use when chatting with close friends, which in turn differs from the register you would use when writing an academic essay or a legal document. Shifts in register can also be used deliberately for rhetorical or humorous effect, a technique known as register-mixing."),

("turn_taking","beginner",
 "I said 'I go school' — is that right?",
 "Almost! We add 'to' — 'I go to school.' Try it once more?",
 "Not quite! The correct sentence is 'I go to school.' In English, we need to use the preposition 'to' before the names of places we are travelling to. This applies not just to school but to many other places like work, the market, the hospital, the park, and so on. There are some exceptions of course — for example, we say 'go home' without 'to'. But for most places, 'to' is required. So the pattern is: subject plus verb 'go' plus 'to' plus destination. Does that make sense to you?"),

("turn_taking","intermediate",
 "I practiced the dialogue last night.",
 "Nice! How did it feel — any parts that still tripped you up?",
 "That's great to hear that you practiced! Consistent practice is really the key to improving in any language. Research in linguistics and language acquisition has shown that spaced repetition and regular exposure to the target language outside of formal learning environments leads to much better retention and fluency than intensive but infrequent study sessions. It's also beneficial to practice in different modalities — listening, speaking, reading, and writing — as each one reinforces different aspects of language competence. If you want, I can now give you a new dialogue to practice or we can review the one you worked on last night."),

("turn_taking","advanced",
 "I'm ready for the next exercise.",
 "Great — here it is. Correct this sentence: 'She insisted to leave early.'",
 "Wonderful! Let's move on to the next exercise then. I have several options for you. We could work on advanced grammar points such as inversion, cleft sentences, or complex conditional structures. Alternatively, we could focus on vocabulary building through discussion of abstract topics, idiom practice, or exploring collocations and word families. Another option would be a speaking fluency exercise where you describe a picture or tell a story within a time limit. We could also do a debate activity where you argue for or against a controversial statement, which is excellent practice for critical thinking in English. What sounds most interesting to you?"),

# ══════════════════════════════════════════════════════════════
# 5. DIFFICULTY CALIBRATION  (matching learner level vs. over/under-shooting)
# ══════════════════════════════════════════════════════════════
("difficulty_calibration","beginner",
 "I want to learn English. I am new student.",
 "Welcome! Let's start easy — can you tell me your name in English?",
 "Great! Let's start with the subjunctive mood, modal verbs in passive constructions, and some advanced discourse markers commonly used in academic English."),

("difficulty_calibration","beginner",
 "What is 'run'?",
 "'Run' means to move fast using your legs. Like when you run in a race!",
 "'Run' is a monosyllabic irregular verb with multiple syntactic functions. As an intransitive verb it takes no direct object, but as a transitive verb it can. It also has a rich set of phrasal verb derivatives."),

("difficulty_calibration","advanced",
 "Can you give me something challenging? I've been learning English for 10 years.",
 "Let's try this — rewrite 'The committee decided to postpone the vote' using a nominalization.",
 "Sure! Let's practice basic colors and numbers. Can you count to ten?"),

("difficulty_calibration","intermediate",
 "I know basic grammar but I get confused with tenses.",
 "Let's pick one tense at a time. Which trips you up most — perfect tenses or conditionals?",
 "Let's cover all twelve English tenses, their aspect types, their relationship to the aspect hypothesis in linguistics, and the distinction between grammatical aspect and lexical aspect."),

("difficulty_calibration","beginner",
 "How do I make a question?",
 "In English, we flip the verb and the subject. So 'You are happy' becomes 'Are you happy?' Let's try one!",
 "Question formation involves auxiliary inversion, do-support for main verb constructions, and wh-fronting in the case of content questions, all governed by syntactic movement rules."),

("difficulty_calibration","advanced",
 "I want to sound more like a native speaker.",
 "Let's focus on weak forms and connected speech — natives reduce words like 'and', 'to', 'of' heavily. Try saying 'cup of tea' naturally.",
 "Say 'Hello, how are you?' ten times for pronunciation practice."),

("difficulty_calibration","intermediate",
 "I sometimes mix up 'borrow' and 'lend'.",
 "'Borrow' is when you take something — 'Can I borrow your pen?' 'Lend' is when you give — 'Can you lend me your pen?' Same situation, different direction!",
 "These are deceptive interlingual synonyms functioning as converse pairs, similar to 'buy/sell' and 'teach/learn', representing directionality in reciprocal semantic frames."),

("difficulty_calibration","beginner",
 "I want to speak about my family.",
 "Perfect topic! Tell me — do you have brothers or sisters?",
 "Excellent. Discuss your family using relative clauses, possessive constructions, and contrast the nuclear family with extended kinship structures in English sociolinguistics."),

("difficulty_calibration","advanced",
 "What's the difference between 'comprise' and 'compose'?",
 "Good one. 'The whole comprises the parts' — the team comprises five players. 'The parts compose the whole' — five players compose the team. The direction flips.",
 "'Comprise' means to include or to be made up of. For example: 'The team comprises five players.' Now try using it in a sentence about your city."),

("difficulty_calibration","intermediate",
 "Can you help me write an email to my boss?",
 "Of course! Let's start with the opening line. How formal is your relationship with your boss?",
 "We need to begin with a nominalized subject complement in the salutation, followed by a hedged illocutionary act in the first clause to position your epistemic stance appropriately."),

]

# ─── EXPANSION TEMPLATES ───────────────────────────────────────────────────────
# These generate many more variations programmatically
VOCAB_WORDS = [
    ("beautiful","nice-looking or pleasing"),("angry","feeling strong displeasure"),
    ("nervous","worried or anxious"),("curious","wanting to know more"),
    ("busy","having a lot to do"),("tired","needing rest"),
    ("excited","feeling happy about something coming"),("bored","not interested"),
    ("proud","happy about an achievement"),("patient","able to wait calmly"),
]

IRREGULAR_VERBS = [
    ("break","broke","broken"),("choose","chose","chosen"),("draw","drew","drawn"),
    ("fall","fell","fallen"),("forget","forgot","forgotten"),("give","gave","given"),
    ("keep","kept","kept"),("know","knew","known"),("leave","left","left"),
    ("meet","met","met"),("ring","rang","rung"),("rise","rose","risen"),
    ("run","ran","run"),("see","saw","seen"),("speak","spoke","spoken"),
    ("stand","stood","stood"),("swim","swam","swum"),("take","took","taken"),
    ("think","thought","thought"),("write","wrote","written"),
]

PHRASAL_VERBS = [
    ("give up","quit or stop trying","I gave up smoking last year."),
    ("look up","search for information","Let me look up that word."),
    ("run into","meet unexpectedly","I ran into my teacher at the market."),
    ("put off","delay something","Don't put off your homework."),
    ("bring up","mention a topic","She brought up a good point."),
    ("carry on","continue","Please carry on with your work."),
    ("come across","find or discover","I came across this book by chance."),
    ("figure out","understand or solve","I can't figure out this problem."),
    ("get along","have a good relationship","Do you get along with your classmates?"),
    ("hold on","wait","Hold on, let me check that."),
    ("keep up","maintain pace","It's hard to keep up with native speakers."),
    ("make up","invent or reconcile","Don't make up excuses."),
    ("point out","indicate or highlight","She pointed out my mistake kindly."),
    ("set up","arrange or establish","Can you set up a meeting for us?"),
    ("show up","arrive","He didn't show up to class today."),
]

PREPOSITION_ERRORS = [
    ("I am good in English","in","at","I am good at English."),
    ("She is married with a doctor","with","to","She is married to a doctor."),
    ("He is interested about music","about","in","He is interested in music."),
    ("We arrived to the station","to","at","We arrived at the station."),
    ("I am bored of studying","bored","bored with","I am bored with studying."),
    ("She explained me the rule","explained me","explained to me","She explained the rule to me."),
    ("I am agree with you","am agree","agree","I agree with you."),
    ("He is looking forward to meet you","to meet","to meeting","He is looking forward to meeting you."),
    ("I am depending of you","depending of","depending on","I am depending on you."),
    ("She is good for cooking","good for","good at","She is good at cooking."),
]

TOPIC_CONTEXTS = [
    ("ordering food at a restaurant","Can I have the chicken curry, please?","What does 'menu' mean?"),
    ("introducing yourself","My name is Priya and I am from Mumbai.","How do I say my job?"),
    ("describing your home","I live in a flat with two bedrooms.","What is the word for a big house?"),
    ("talking about hobbies","I enjoy playing cricket on weekends.","How do I say I like music?"),
    ("asking for directions","Excuse me, how do I get to the station?","What does 'turn left' mean?"),
    ("shopping at a market","How much does this cost?","Can I try a smaller size?"),
    ("talking about work","I work as an engineer at a tech company.","My job is very busy nowadays."),
    ("discussing the weather","It's very hot today, isn't it?","I hope it rains soon."),
    ("making plans with a friend","Are you free this Saturday?","Let's meet at the coffee shop."),
    ("describing a person","She has long dark hair and a bright smile.","He is very tall and kind."),
]

ROLEPLAY_SCENARIOS = [
    ("doctor visit","I have had a headache for two days.","beginner"),
    ("job interview","Tell me about your greatest strength.","intermediate"),
    ("airport check-in","I would like a window seat, please.","beginner"),
    ("hotel complaint","The air conditioning in my room is not working.","intermediate"),
    ("phone call","Could I speak to Mr. Sharma, please?","intermediate"),
    ("class presentation","Today I will talk about climate change.","advanced"),
    ("customer service","I ordered this last week and it still hasn't arrived.","intermediate"),
    ("pharmacy","I need something for a cold.","beginner"),
    ("bank","I would like to open a savings account.","intermediate"),
    ("negotiating a deadline","Would it be possible to have two more days?","advanced"),
]

LISTENING_COMPREHENSION = [
    ("The speaker said the meeting is at 3 PM. What time is the meeting?","Three o'clock in the afternoon — or 15:00 if you use the 24-hour clock. Did you catch that?","The meeting is at 3 PM. This is a factual comprehension question testing your ability to identify specific information in spoken discourse."),
    ("You heard 'turn right at the pharmacy'. What do you do at the pharmacy?","You turn right when you reach the pharmacy — it's your signal to change direction. Make sense?","At the pharmacy, you execute a 90-degree directional change to the right, indicating spatial navigation based on a landmark reference."),
]

pairs = list(SEED_PAIRS)

# ─── VOCABULARY PAIRS ──────────────────────────────────────────────────────────
for word, meaning in VOCAB_WORDS:
    pairs.append(("verbosity","beginner",
        f"What does '{word}' mean?",
        f"'{word.capitalize()}' means {meaning}. Can you use it in a sentence?",
        f"The word '{word}' is an adjective in English with its roots in Latin and Old French. It has multiple connotations and can be used in formal and informal registers. The precise definition varies slightly by context but broadly refers to {meaning}. It is frequently used in everyday English conversation as well as in literature and academic writing."))

# ─── IRREGULAR VERB PAIRS ──────────────────────────────────────────────────────
for base, past, pp in IRREGULAR_VERBS:
    # scaffolding pair
    pairs.append(("scaffolding","beginner",
        f"What is the past tense of '{base}'?",
        f"Try saying '{base}' with '-ed' added — does that sound natural to you? Most learners notice it doesn't, which is the clue it's irregular.",
        f"The past tense of '{base}' is '{past}' and the past participle is '{pp}'. It is an irregular verb and must be memorized."))
    # error correction pair
    pairs.append(("error_correction","beginner",
        f"I have {past} the exam.",
        f"Almost! For 'have + {base}', we use the past participle '{pp}' — so 'I have {pp} the exam.' Try it!",
        f"Wrong. You cannot use '{past}' after 'have'. The correct form is the past participle '{pp}'. Say 'I have {pp} the exam.'"))

# ─── PHRASAL VERB PAIRS ────────────────────────────────────────────────────────
for pv, meaning, example in PHRASAL_VERBS:
    pairs.append(("verbosity","intermediate",
        f"What does '{pv}' mean?",
        f"'{pv.capitalize()}' means to {meaning}. Like: '{example}' — want to try your own?",
        f"The phrasal verb '{pv}' is a multi-word verb composed of the base verb and one or more particles. Its idiomatic meaning, which is '{meaning}', cannot be deduced from the individual components. Here is a list of example sentences, usage contexts, register levels, and related phrasal verbs that share similar semantic fields: {example} This phrasal verb appears frequently in both formal and informal registers and is essential for achieving native-like fluency."))
    pairs.append(("scaffolding","intermediate",
        f"How do I use '{pv}' in a sentence?",
        f"Good question! What's a situation in your life where you might {meaning}? Try building a sentence from that.",
        f"Here is how you use '{pv}': {example} Now, '{pv}' means to {meaning}. It can be used in many contexts."))

# ─── PREPOSITION ERROR PAIRS ───────────────────────────────────────────────────
for wrong_sent, wrong_prep, right_prep, correct_sent in PREPOSITION_ERRORS:
    pairs.append(("error_correction","intermediate",
        wrong_sent,
        f"Really close! The preposition here is '{right_prep}' rather than '{wrong_prep}'. So: '{correct_sent}' — try it!",
        f"Incorrect preposition. '{wrong_prep}' is wrong here. The correct preposition is '{right_prep}'. The correct sentence is: '{correct_sent}'"))
    pairs.append(("difficulty_calibration","intermediate",
        f"Is this correct: '{wrong_sent}'?",
        f"Almost! Just one small fix — which preposition do you think fits better here?",
        f"No, this is incorrect. The correct preposition in this construction is '{right_prep}' not '{wrong_prep}' due to the collocational properties of the adjective and the semantic role of the prepositional phrase."))

# ─── TOPIC/CONTEXT PAIRS ───────────────────────────────────────────────────────
for topic, sample_sent, sample_q in TOPIC_CONTEXTS:
    pairs.append(("turn_taking","beginner",
        f"I want to practice {topic}. {sample_q}",
        f"Great topic! Let's jump right in. Say your first line and I'll respond.",
        f"Excellent choice! When {topic}, there are many phrases and structures you will need to know. Let me first walk you through all of them comprehensively before we practice."))
    pairs.append(("scaffolding","intermediate",
        f"How do I talk naturally about {topic}?",
        f"Let's try it! Imagine you're in that situation right now and say the first thing that comes to mind.",
        f"When discussing {topic}, there are several key phrases, vocabulary items, and grammatical structures that are commonly used by native speakers. Let me list all of them for you."))

# ─── ROLEPLAY PAIRS ────────────────────────────────────────────────────────────
for scenario, opening_line, level in ROLEPLAY_SCENARIOS:
    pairs.append(("turn_taking", level,
        f"Let's roleplay a {scenario}. I'll start: {opening_line}",
        f"Sure! I'll play the other person. Go ahead — I'm ready.",
        f"Great! Before we begin the roleplay, let me explain all the vocabulary and phrases you might need in a {scenario} situation, as well as the cultural norms and conventions that typically apply in such interactions in English-speaking countries."))
    pairs.append(("verbosity", level,
        opening_line,
        "Of course! How can I help you today?",
        f"Welcome! In the context of a {scenario}, the phrase you just used is quite appropriate and demonstrates an understanding of the pragmatic conventions governing such institutional discourse. Your use of politeness markers and appropriate register is commendable."))

# ─── LISTENING COMPREHENSION PAIRS ─────────────────────────────────────────────
for q, chosen, rejected in LISTENING_COMPREHENSION:
    pairs.append(("verbosity","beginner", q, chosen, rejected))

# ─── EXTRA CALIBRATION PAIRS ───────────────────────────────────────────────────
advanced_challenges = [
    ("Can you give me a tongue twister?",
     "Here's one: 'She sells seashells by the seashore.' Try it slowly first, then speed up!",
     "Certainly! Tongue twisters are alliterative or rhyming phrases designed to challenge articulation and phonological processing. Here is one: 'She sells seashells by the seashore.' The phonological complexity arises from the alternation between /s/ and /ʃ/ phonemes."),
    ("What's a good way to sound more confident when speaking?",
     "Slow down a little and don't rush your sentences — confidence often sounds like calm, not speed.",
     "Confident speech in English involves prosodic features including strategic pausing, controlled speech rate, appropriate pitch variation, clear articulation at consonant boundaries, and the judicious use of discourse markers to signal cohesion and fluency."),
    ("I freeze when speaking to native speakers.",
     "That's really common! What usually triggers it — is it specific words, or the speed they talk at?",
     "Communication apprehension in L2 speakers is well-documented in second language acquisition research. It may stem from anxiety related to negative evaluation, unfamiliarity with native speaker norms, processing speed limitations, or working memory constraints during real-time production."),
    ("How do I use stress in sentences?",
     "In English we naturally stress the most important word. Try: 'I WANT coffee' vs 'I want COFFEE' — hear the difference?",
     "Sentence stress in English operates at the interface of phonology and pragmatics. Content words typically receive primary stress while function words are reduced. Nuclear stress placement signals information structure, particularly the distinction between given and new information in discourse."),
    ("Is 'anyways' correct English?",
     "It's used in casual speech but 'anyway' without the 's' is the standard form for writing and formal speech.",
     "'Anyways' is a dialectal variant of the standard form 'anyway'. While attested in informal registers and certain regional dialects, particularly in North American English, it is generally considered non-standard and is therefore inadvisable in formal written or spoken contexts."),
]

for prompt, chosen, rejected in advanced_challenges:
    pairs.append(("verbosity","advanced", prompt, chosen, rejected))

# Extra scaffolding pairs for advanced learners
adv_scaffold = [
    ("How do I write a strong thesis statement?",
     "What's the main argument you want to make? Start there and we'll shape it.",
     "A strong thesis statement should clearly state your position, be specific and debatable, and preview your main supporting points."),
    ("I'm not sure how to conclude a presentation.",
     "What's the most important thing you want them to remember? Start your conclusion from that.",
     "A good conclusion should summarize your main points, restate your thesis, and end with a call to action or memorable statement."),
    ("How do I disagree politely in English?",
     "Think about how you'd soften a 'no' in your own language — English uses similar strategies. What word might you add to make 'I disagree' softer?",
     "You can use phrases like 'I see your point, but…', 'I'm not sure I agree…', or 'That's interesting, though I think…'"),
]
for prompt, chosen, rejected in adv_scaffold:
    pairs.append(("scaffolding","advanced", prompt, chosen, rejected))

# Extra turn-taking for intermediate
int_turn = [
    ("I think I'm ready to try the next level.",
     "Let's see! Try this sentence and we'll know for sure.",
     "Wonderful! Moving to the next level means we'll now cover a wider range of topics, grammar structures, and vocabulary. Let me outline what the intermediate level typically involves and what you can expect from our sessions going forward."),
    ("I'm getting better at pronunciation.",
     "I can hear it! Which sound gave you the most trouble before?",
     "That's fantastic progress! Pronunciation improvement involves work on individual phonemes, consonant clusters, vowel reduction, word stress, sentence rhythm, and intonation patterns. All of these contribute to your overall intelligibility and naturalness as a speaker."),
]
for prompt, chosen, rejected in int_turn:
    pairs.append(("turn_taking","intermediate", prompt, chosen, rejected))

# ─── ADDITIONAL EXPANSION TEMPLATES ──────────────────────────────────────────
# These fill the gap to 500+ high-quality pairs, targeting underrepresented
# dimensions (difficulty_calibration, turn_taking) and the advanced level.

# --- Common grammar mistakes (error_correction, mixed levels) ---------------
GRAMMAR_MISTAKES = [
    ("beginner", "I am agree with you.", "am agree", "agree",
     "I agree with you."),
    ("beginner", "He have a big house.", "have", "has",
     "He has a big house."),
    ("beginner", "She can sings well.", "can sings", "can sing",
     "She can sing well."),
    ("beginner", "I am go to school.", "am go", "go",
     "I go to school."),
    ("beginner", "They was happy.", "was", "were",
     "They were happy."),
    ("beginner", "I no like this.", "no like", "don't like",
     "I don't like this."),
    ("beginner", "Where you are going?", "you are", "are you",
     "Where are you going?"),
    ("beginner", "He always is late.", "always is", "is always",
     "He is always late."),
    ("intermediate", "I am used to go there every day.", "used to go", "used to going",
     "I am used to going there every day."),
    ("intermediate", "She told that she was tired.", "told that", "said that",
     "She said that she was tired."),
    ("intermediate", "He made me to wait.", "made me to wait", "made me wait",
     "He made me wait."),
    ("intermediate", "I wish I can fly.", "can", "could",
     "I wish I could fly."),
    ("intermediate", "The news are shocking.", "are", "is",
     "The news is shocking."),
    ("intermediate", "He is knowing the answer already.", "is knowing", "knows",
     "He knows the answer already."),
    ("intermediate", "I will going to the store.", "will going", "am going",
     "I am going to the store."),
    ("intermediate", "She suggested him to leave.", "him to leave", "that he leave",
     "She suggested that he leave."),
    ("advanced", "Not only she arrived late, but she also forgot the documents.",
     "Not only she arrived", "Not only did she arrive",
     "Not only did she arrive late, but she also forgot the documents."),
    ("advanced", "He denied to take the money.", "denied to take", "denied taking",
     "He denied taking the money."),
    ("advanced", "Scarcely I had sat down when the phone rang.",
     "Scarcely I had", "Scarcely had I",
     "Scarcely had I sat down when the phone rang."),
    ("advanced", "The less students attend, the worse the outcome.",
     "less students", "fewer students",
     "The fewer students attend, the worse the outcome."),
]

for lvl, wrong_sent, wrong_part, right_part, correct_sent in GRAMMAR_MISTAKES:
    pairs.append(("error_correction", lvl,
        wrong_sent,
        f"Almost there! Swap '{wrong_part}' with '{right_part}' — so: '{correct_sent}' Try it!",
        f"Incorrect. '{wrong_part}' is wrong. The correct form is '{right_part}'. The sentence is: '{correct_sent}'"))

# --- Confusable word pairs (difficulty_calibration, mixed levels) ------------
CONFUSABLE_WORDS = [
    ("beginner", "say", "tell",
     "What's the difference between 'say' and 'tell'?",
     "'Say' focuses on the words — 'She said hello.' 'Tell' needs a person — 'She told me hello.' Try one!",
     "'Say' is used without an indirect object while 'tell' requires one. The syntactic frames are: say + clause/NP vs tell + NP_indirect + clause/NP_direct. This is a valency distinction in argument structure."),
    ("beginner", "come", "go",
     "When do I use 'come' versus 'go'?",
     "'Come' is toward the speaker — 'Come here!' 'Go' is away — 'Go there!' Where are you? That's the trick.",
     "'Come' and 'go' are deictic motion verbs whose usage depends on the spatial and temporal perspective of the discourse participants relative to the goal of motion."),
    ("beginner", "look", "see", "watch",
     "What's the difference between 'look', 'see', and 'watch'?",
     "'See' happens naturally — your eyes do it. 'Look' is on purpose — you choose to. 'Watch' means you keep looking for a while. Which one fits TV?",
     "'Look', 'see', and 'watch' are perception verbs differentiated by volitionality and duration. 'See' is non-volitional and punctual, 'look' is volitional and momentary, and 'watch' is volitional and durative."),
    ("intermediate", "affect", "effect",
     "I always mix up 'affect' and 'effect'.",
     "'Affect' is the verb — it does something. 'Effect' is the noun — it's the result. 'The rain affects my mood. The effect is I stay home.'",
     "'Affect' functions primarily as a transitive verb meaning to influence or have an impact on, while 'effect' functions primarily as a noun denoting a result, consequence, or outcome. However, 'effect' can also be used as a verb meaning to bring about, and 'affect' can be a noun in psychology referring to observable emotional response."),
    ("intermediate", "rob", "steal",
     "What is the difference between 'rob' and 'steal'?",
     "'Rob' takes the victim — 'They robbed the bank.' 'Steal' takes the thing — 'They stole the money.' The object flips!",
     "'Rob' and 'steal' differ in their argument structure: 'rob' takes an animate or institutional patient as its direct object while 'steal' takes the theme (the thing taken) as its direct object."),
    ("intermediate", "lay", "lie",
     "I get confused between 'lay' and 'lie'.",
     "'Lay' needs an object — you lay something down. 'Lie' doesn't — you lie down yourself. Can you try a sentence with each?",
     "'Lay' is a transitive verb requiring a direct object (lay/laid/laid) while 'lie' is intransitive (lie/lay/lain). The confusion is compounded by the fact that the past tense of 'lie' is homophonous with the base form of 'lay'."),
    ("advanced", "infer", "imply",
     "What's the difference between 'infer' and 'imply'?",
     "The speaker implies — they hint at something. The listener infers — they figure it out. Direction matters: out vs. in.",
     "'Imply' is a speech act performed by the speaker involving conversational implicature, while 'infer' is a cognitive process performed by the hearer involving pragmatic inference from contextual cues."),
    ("advanced", "comprise", "consist",
     "When should I use 'comprises' versus 'consists of'?",
     "'The team comprises five players' = the whole includes the parts. 'The team consists of five players' = same idea, just with 'of'. Never say 'comprised of'!",
     "'Comprise' is a holonymic verb where the subject denotes the whole and the object denotes the parts, without a preposition. 'Consist of' reverses the frame. 'Is comprised of' is a passive construction considered nonstandard by prescriptivists."),
    ("advanced", "farther", "further",
     "Is there a real difference between 'farther' and 'further'?",
     "'Farther' is physical distance — 'The store is farther away.' 'Further' is abstract — 'Let's discuss this further.' In casual speech, most people use 'further' for both.",
     "'Farther' is conventionally reserved for literal, measurable spatial distance while 'further' is used for figurative, metaphorical, or abstract extension. However, this distinction is maintained more strictly in American English; British English tends to use 'further' for both senses."),
    ("beginner", "fun", "funny",
     "Is 'fun' and 'funny' the same?",
     "'Fun' means enjoyable — 'The party was fun.' 'Funny' means it makes you laugh — 'The joke was funny.' Not the same!",
     "'Fun' is a noun/adjective denoting enjoyment or amusement in a general sense, while 'funny' is an adjective specifically connoting humor or strangeness. Their semantic fields overlap but are not coextensive."),
    ("beginner", "hear", "listen",
     "What is the difference between 'hear' and 'listen'?",
     "'Hear' is automatic — your ears do it. 'Listen' is a choice — you pay attention on purpose. Which one happens when a loud noise startles you?",
     "'Hear' is an involuntary perception verb while 'listen' is a volitional activity verb. The distinction maps onto the stative/dynamic contrast in English aspectual classification."),
]

for item in CONFUSABLE_WORDS:
    if len(item) == 6:
        lvl, w1, w2, prompt, chosen, rejected = item
    else:
        lvl, w1, w2, w3, prompt, chosen, rejected = item
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Pronunciation / speaking scenarios (verbosity + turn_taking, mixed) -----
PRONUNCIATION_SCENARIOS = [
    ("beginner", "How do I pronounce 'th'?",
     "Put your tongue between your teeth and blow gently. Try 'the' — feel the vibration?",
     "The 'th' sound in English comprises two phonemes: the voiced dental fricative /ð/ as in 'the' and the voiceless dental fricative /θ/ as in 'think'. Production requires placing the tongue tip against the upper front teeth while directing the airstream through the narrow channel."),
    ("beginner", "I can't say 'world' properly.",
     "It's tricky! Start with 'wer' then add 'ld' — say it slowly: wer-ld. Speed up when it feels natural.",
     "The word 'world' contains a challenging consonant cluster /rld/ in the coda position. The rhotic approximant /r/ combined with the lateral approximant /l/ and the alveolar stop /d/ creates articulatory complexity."),
    ("beginner", "How do I say 'comfortable'?",
     "Most people say 'KUMF-ter-bul' — just three syllables, not four. The 'or' disappears. Try it!",
     "The word 'comfortable' undergoes syllable reduction in connected speech, typically realized as three syllables rather than four in most dialects."),
    ("intermediate", "Why do English speakers eat their words?",
     "It's called connected speech — words blend together. 'Want to' becomes 'wanna'. Let's practice hearing some of these.",
     "Connected speech processes include assimilation, elision, liaison, and reduction. These phenomena occur at word boundaries and are governed by phonological rules."),
    ("intermediate", "How do I sound less robotic when speaking?",
     "Try varying your pitch — go up at interesting parts, down at endings. Read this sentence and exaggerate the ups and downs.",
     "Natural-sounding speech requires mastery of suprasegmental features including pitch variation, rhythm, stress timing, and appropriate use of pausing and intonation contours."),
    ("advanced", "How can I reduce my accent?",
     "Which specific sounds feel different from native speakers? Let's pick one and work on it rather than trying to change everything at once.",
     "Accent reduction involves systematic modification of L1-influenced phonological patterns through contrastive analysis, perception training, articulatory exercises, and prosodic modeling."),
    ("advanced", "I want to learn sarcasm in English.",
     "Sarcasm is mostly in the tone — you say the opposite of what you mean with a flat or exaggerated voice. Try saying 'Oh, great' like you mean 'Oh, terrible.'",
     "Sarcasm in English is a pragmatic phenomenon involving the use of verbal irony, where the propositional content of an utterance is at odds with the speaker's communicative intent."),
    ("intermediate", "People don't understand me even though my grammar is correct.",
     "That often comes down to word stress. Where you put the emphasis changes the meaning. Let's practice — say 'REcord' and 'reCORD'. Hear the difference?",
     "Intelligibility issues despite grammatical accuracy often stem from prosodic transfer, including incorrect lexical stress assignment, inappropriate sentence rhythm, and non-target-like intonation patterns."),
]

for lvl, prompt, chosen, rejected in PRONUNCIATION_SCENARIOS:
    pairs.append(("verbosity", lvl, prompt, chosen, rejected))

# --- Conversation starters / small talk (turn_taking, mixed levels) ----------
SMALL_TALK_SCENARIOS = [
    ("beginner", "How do I start a conversation with someone?",
     "Start simple! A comment about where you are works great — 'Nice weather today!' or 'Is this seat taken?' What situation are you thinking of?",
     "Conversation initiation in English follows specific pragmatic conventions. There are several types of openers: phatic communion such as comments about weather or the immediate environment, self-introductions, compliments, questions about shared context, and references to shared experiences. The choice of opener depends on the social distance, power dynamics, and contextual appropriateness."),
    ("beginner", "What do I say when someone asks 'How are you?'",
     "Usually just 'Good, thanks! And you?' — it's more greeting than real question. Want to practice a few variations?",
     "When someone asks 'How are you?' in English, it is typically a formulaic greeting rather than a genuine inquiry about your wellbeing. Standard responses include 'Fine, thank you', 'Good, thanks', 'I'm doing well, thank you for asking', 'Not bad', 'Can't complain', and many others depending on formality and register."),
    ("intermediate", "How do I politely end a conversation?",
     "Wrap up with 'Well, it was nice chatting!' or 'I should get going.' Signal it gently. Want to roleplay an exit?",
     "Conversation closing in English involves a series of pre-closing signals and closing sequences. Typical pre-closing moves include summarization, arrangement for future contact, well-wishing, and assessment of the conversation."),
    ("intermediate", "How do I keep a conversation going when I run out of things to say?",
     "Ask about what they just said — 'Oh really? What happened then?' People love talking about themselves. Try it!",
     "Conversation maintenance strategies include topic recycling, topic shifting, backchannel responses, clarification requests, and formulating new adjacency pairs."),
    ("advanced", "How do I handle awkward silences?",
     "A short silence is fine — don't panic! You can say 'So anyway...' to change topic, or ask 'What have you been up to?' Silence feels longer to you than to them.",
     "Silence in conversation is a complex pragmatic phenomenon. In English, pauses longer than approximately one second may be perceived as uncomfortable lapses. Repair strategies include topic-shift markers, meta-comments about the silence, and the deployment of formulaic sequences."),
    ("advanced", "How do I interrupt politely in English?",
     "Try 'Sorry, can I jump in?' or 'Just to add to that...' — acknowledging the other person while taking the turn. Practice with me?",
     "Polite interruption in English involves the use of mitigating devices such as apology formulae, hedged performatives, and collaborative overlap."),
    ("beginner", "I'm scared to speak English with strangers.",
     "That's totally normal! Start with short interactions — ordering coffee, saying hi. What's a real situation you'll be in soon?",
     "Foreign language anxiety is a well-documented affective variable in second language acquisition. It encompasses communication apprehension, test anxiety, and fear of negative evaluation. Research suggests several intervention strategies."),
    ("intermediate", "How do I make my English sound more natural in daily life?",
     "Use short forms! 'Gonna' instead of 'going to', 'wanna' instead of 'want to'. Also, small words like 'well', 'so', 'you know' make you sound human. Try adding one!",
     "Achieving naturalness in spoken English requires the integration of contracted forms, informal lexis, discourse markers, vague language, hedging devices, and appropriate register shifting."),
]

for lvl, prompt, chosen, rejected in SMALL_TALK_SCENARIOS:
    pairs.append(("turn_taking", lvl, prompt, chosen, rejected))

# --- Difficulty calibration: level-mismatch scenarios ----------------------
CALIBRATION_MISMATCH = [
    ("beginner", "I just started learning English this week.",
     "Welcome! Let's start with greetings. Can you say 'My name is...' and tell me your name?",
     "Let's begin with an overview of the English tense system, covering all twelve tenses across four aspects."),
    ("beginner", "I only know a few words like 'hello' and 'yes'.",
     "That's a great start! Let's add a few more — how about 'please', 'thank you', and 'sorry'? Try saying them!",
     "Good foundation! Now let's work on constructing complex sentences with subordinate clauses and relative pronouns."),
    ("beginner", "Numbers are hard for me.",
     "Let's count together! One, two, three... now you try from four. Take your time!",
     "Numbers in English follow a decimal system with irregular forms from one to twelve, teen-forms from thirteen to nineteen, and decadal forms thereafter."),
    ("beginner", "I want to learn colors.",
     "Fun topic! Point at something near you — what color is it? I'll tell you the English word.",
     "Colors in English comprise both basic color terms as identified by Berlin and Kay's universalist hierarchy and numerous secondary terms."),
    ("beginner", "What is 'apple'?",
     "An apple is a fruit — round, usually red or green. Do you like apples?",
     "An apple is a pome fruit of the genus Malus in the family Rosaceae. The word derives from Proto-Germanic."),
    ("intermediate", "I can read English but speaking is hard.",
     "That's super common! Let's just talk — tell me about your day today and don't worry about mistakes.",
     "The discrepancy between receptive and productive skills is attributable to the different processing demands of decoding versus encoding."),
    ("intermediate", "I want to improve my email writing.",
     "Great goal! What kind of emails — to your boss, to a friend, or something else?",
     "Email writing requires mastery of epistolary conventions, hedging strategies, politeness formulae, and register-appropriate lexis across formal, semi-formal, and informal registers."),
    ("intermediate", "I need English for my job in customer service.",
     "Perfect! Let's practice the most common situation first — a customer asking for help. What do you usually need to say?",
     "Customer service English encompasses speech acts including greeting, information elicitation, problem diagnosis, solution proposal, and closing. Each requires specific illocutionary strategies."),
    ("advanced", "I want to improve my academic writing.",
     "What are you writing — an essay, thesis, or research paper? Let's look at the structure together.",
     "Tell me what colors you know in English. Can you name five colors?"),
    ("advanced", "I need to prepare for a debate competition.",
     "Great! Let's start with your opening argument. State your position in one sentence — we'll sharpen it from there.",
     "Let's practice basic question formation. Can you make a question from 'She is happy'?"),
    ("advanced", "How do I use hedging language in academic papers?",
     "Words like 'might', 'tends to', 'appears to' soften your claims. Try rewriting 'This proves X' using a hedge.",
     "What is a noun? A noun is a word for a person, place, or thing."),
    ("advanced", "I'm preparing for the IELTS speaking test.",
     "Which part worries you most — the personal questions, the long turn, or the discussion? Let's target that.",
     "Let's start by learning the alphabet. A, B, C... can you continue?"),
    ("intermediate", "I understand movies without subtitles now!",
     "That's a big milestone! What did you watch recently? Any phrases that stuck with you?",
     "Audiovisual comprehension without textual support indicates development of top-down processing skills, automatic lexical access, and tolerance of ambiguity in connected speech streams."),
    ("beginner", "English spelling is so confusing!",
     "It really is! Let's focus on the most useful words first. Which words do you need to write the most?",
     "English orthography is notoriously opaque due to historical sound changes that were not reflected in the spelling system, combined with extensive borrowing from French, Latin, Greek, and other languages."),
    ("intermediate", "I want to understand song lyrics better.",
     "Great idea! What's a song you like? We can look at the lyrics together and break down any tricky parts.",
     "Song lyrics in English frequently employ poetic license, including non-standard syntax, lexical creativity, phonological distortion for rhyme and meter, and cultural allusions requiring encyclopedic knowledge."),
]

for lvl, prompt, chosen, rejected in CALIBRATION_MISMATCH:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Idiom and expression pairs (scaffolding, intermediate+advanced) --------
IDIOMS = [
    ("intermediate", "break the ice",
     "What does 'break the ice' mean?",
     "Think about it — when you meet strangers, there's awkward tension, like a frozen surface. What would 'breaking' that mean?",
     "'Break the ice' means to relieve tension or get conversation going in an awkward social situation."),
    ("intermediate", "hit the nail on the head",
     "I heard someone say 'hit the nail on the head'. What does that mean?",
     "Picture hammering — when you hit the nail perfectly, it goes in right. So if someone says that about your comment, what do you think they mean?",
     "It means to describe exactly what is causing a situation or problem. It comes from carpentry."),
    ("intermediate", "a piece of cake",
     "My friend said the test was 'a piece of cake'. What?",
     "Imagine eating cake — is it hard or easy? So when something is 'a piece of cake'...",
     "'A piece of cake' is an idiom meaning something is very easy."),
    ("intermediate", "cost an arm and a leg",
     "What does 'cost an arm and a leg' mean?",
     "If you had to give an arm and a leg for something — that's a huge price, right? What kind of thing might someone describe that way?",
     "It means something is very expensive. It is a hyperbolic idiomatic expression."),
    ("advanced", "the ball is in your court",
     "Someone told me 'the ball is in your court' after a negotiation.",
     "Think about tennis — when the ball is on your side, it's your turn to hit. So in the negotiation, whose move is it now?",
     "This idiom means it's your turn to take action or make a decision. It derives from tennis."),
    ("advanced", "burn the midnight oil",
     "What does 'burning the midnight oil' mean?",
     "Before electricity, people used oil lamps. If you're burning oil at midnight, what are you doing?",
     "It means to work late into the night. The expression dates back to the era when oil lamps were used for illumination."),
    ("advanced", "read between the lines",
     "What does 'read between the lines' mean?",
     "If the real message isn't in the words themselves, where would it be? Between them! What situation might require that?",
     "'Read between the lines' means to look for a hidden meaning in something said or written that is not explicitly stated."),
    ("intermediate", "pull someone's leg",
     "Is 'pulling my leg' a bad thing?",
     "Not at all! If a friend says something unbelievable with a smile — they might be pulling your leg. What do you think that means?",
     "'Pull someone's leg' means to joke with or tease someone by saying something untrue in a playful manner."),
    ("intermediate", "under the weather",
     "My colleague said she's 'under the weather'. Is she sad?",
     "Not exactly — think about how bad weather makes you feel. Cold, not great. So if she's 'under the weather'...",
     "This idiom means feeling ill or sick. It originates from nautical terminology."),
    ("advanced", "play devil's advocate",
     "What does 'play devil's advocate' mean?",
     "Imagine arguing the opposite side just to test an idea — not because you believe it. When might that be useful?",
     "It means to argue against an idea for the sake of debate, even if you agree with it. The term originates from a Catholic Church practice."),
]

for lvl, idiom, prompt, chosen, rejected in IDIOMS:
    pairs.append(("scaffolding", lvl, prompt, chosen, rejected))

# --- Writing & formal English (verbosity, intermediate+advanced) ------------
WRITING_PAIRS = [
    ("intermediate", "How do I start a formal email?",
     "'Dear Mr./Ms. [Name],' if you know them. 'Dear Sir or Madam,' if you don't. Then state your purpose in the first line.",
     "Formal email salutations in English follow a hierarchical system of address forms. The choice of salutation depends on several factors including the relationship between correspondents, the institutional context, cultural norms, gender considerations, and the degree of formality required by the communicative situation."),
    ("intermediate", "How do I end a formal letter?",
     "'Yours sincerely' if you know their name, 'Yours faithfully' if you don't. Then your name on the next line.",
     "Valedictions in formal English correspondence follow convention-based rules. Common closings include 'Yours sincerely', 'Yours faithfully', 'Kind regards', 'Best regards', and 'Respectfully'. The choice depends on the level of formality, the salutation used, and the nature of the professional relationship."),
    ("advanced", "How do I make my writing more concise?",
     "Cut filler words like 'very', 'really', 'basically'. Replace weak verbs — 'make a decision' becomes 'decide'. Try shortening this: 'Due to the fact that it was raining...'",
     "Concision in writing involves the elimination of redundancy, tautology, circumlocution, and prolixity. Strategies include nominalization reduction, passive-to-active conversion, deletion of empty modifiers, and syntactic compression."),
    ("advanced", "What's the difference between formal and informal writing?",
     "Formal avoids contractions, uses full words ('therefore' not 'so'), and has longer sentences. Informal is closer to how you speak. Try rewriting 'I can't come' formally.",
     "Formal and informal registers in English differ across multiple linguistic dimensions including lexical choice, syntactic complexity, pronoun usage, contraction frequency, hedging strategies, discourse markers, and the deployment of metadiscoursal resources."),
    ("intermediate", "How do I write a complaint email?",
     "Start polite but clear: 'I am writing to express my concern about...' What are you complaining about? Let's draft it together.",
     "Complaint letters in English employ specific speech act sequences including identification of the problem, narration of events, expression of dissatisfaction, and articulation of desired remediation."),
    ("advanced", "How do I write a persuasive argument?",
     "Start with your strongest point, back it with evidence, then address the other side. What's your topic?",
     "Persuasive argumentation in English draws on rhetorical strategies including ethos, pathos, and logos. The organization typically follows classical rhetorical structure: exordium, narratio, confirmatio, refutatio, and peroratio."),
    ("intermediate", "Is it okay to use 'I think' in an essay?",
     "In academic essays, try 'It could be argued that...' or 'Evidence suggests...' instead. But in an opinion piece, 'I think' is fine! What are you writing?",
     "The use of first-person pronouns in academic discourse has been debated extensively in applied linguistics and composition studies. Different style guides and disciplinary conventions offer varying recommendations."),
    ("beginner", "How do I write my address in English?",
     "Start with your name, then house number and street, then city, then country. Like:\nJohn Smith\n123 Main Street\nLondon, UK",
     "Address formatting in English follows conventions that vary by country and postal system. In the UK, addresses follow a specific hierarchy including addressee name, building number, street name, locality, post town, and postcode."),
]

for lvl, prompt, chosen, rejected in WRITING_PAIRS:
    pairs.append(("verbosity", lvl, prompt, chosen, rejected))

# --- Cultural context pairs (difficulty_calibration, mixed) -----------------
CULTURAL_PAIRS = [
    ("beginner", "Why do English people talk about weather so much?",
     "It's just an easy way to start a conversation! You can do it too — 'Nice day, isn't it?' is always safe.",
     "Phatic communion about meteorological conditions is a deeply ingrained pragmatic convention in English-speaking cultures, particularly in Britain."),
    ("intermediate", "What does 'cheers' mean? Someone said it when leaving.",
     "'Cheers' is super flexible — it can mean 'thanks', 'goodbye', or the toast before drinking. Context tells you which!",
     "'Cheers' is a polysemous pragmatic marker in British English that functions as a speech act of thanking, leave-taking, or toasting depending on contextual and sequential parameters."),
    ("intermediate", "Is it rude to ask someone's age in English?",
     "Generally yes, especially with adults you don't know well. You can ask kids though! When in doubt, don't ask.",
     "Age inquiry in English-speaking cultures is governed by politeness conventions rooted in face theory. Asking about age threatens the addressee's negative face."),
    ("advanced", "How do English speakers use sarcasm?",
     "Usually by saying the opposite with a flat tone. 'Oh wonderful' when something bad happens. The tone does all the work — try it!",
     "Sarcasm in English is a form of verbal irony where the intended meaning is the opposite of the literal propositional content. Detection relies on prosodic cues, contextual incongruity, and shared pragmatic knowledge."),
    ("beginner", "What does 'How do you do?' mean?",
     "It's a very formal greeting — you just reply 'How do you do?' back! It doesn't mean 'How are you?' really.",
     "'How do you do?' is a formulaic greeting used in formal British English social introductions. The expected response is the same phrase, not a description of one's state."),
    ("advanced", "How do I navigate office small talk in English?",
     "Stick to safe topics: weekend plans, weather, sports, food. Avoid politics, salary, or personal questions. Ask 'How was your weekend?' on Monday — it always works.",
     "Workplace small talk in English operates within a complex system of face management, rapport building, and relational maintenance."),
]

for lvl, prompt, chosen, rejected in CULTURAL_PAIRS:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Multi-turn context pairs (scaffolding + turn_taking, advanced) ---------
MULTI_TURN_ADVANCED = [
    ("scaffolding", "advanced",
     "I wrote: 'The company has been grew rapidly.' Is this correct?",
     "You're mixing tenses. You've got 'has been' which needs a present participle — what form of 'grow' ends in '-ing'?",
     "No, this is incorrect. 'Has been grew' mixes present perfect continuous with a past tense form. The correct form is 'has been growing' or 'has grown rapidly.'"),
    ("scaffolding", "advanced",
     "How do I use 'whom' correctly?",
     "Try this trick — if you can replace it with 'him', use 'whom'. If 'he' fits, use 'who'. Test it: 'To ___ it may concern' — would you say 'it may concern he' or 'him'?",
     "'Whom' is the objective case of 'who'. It is used when the pronoun functions as the object of a verb or preposition."),
    ("turn_taking", "advanced",
     "I've been studying phrasal verbs and they're overwhelming.",
     "I get it — there are thousands! Which ones come up most in your daily life? Let's focus on those first.",
     "Phrasal verbs are indeed one of the most challenging aspects of English for learners. There are estimated to be over 5,000 phrasal verbs in English. They can be divided into several categories: separable transitive, inseparable transitive, and intransitive. The particles can be adverbs or prepositions. Some phrasal verbs are informal while others are used across registers."),
    ("turn_taking", "advanced",
     "My essay got a low grade for 'lacking cohesion'. What does that mean?",
     "It means the ideas don't flow smoothly from one to the next. Can you share a paragraph? I'll show you where to add connectors.",
     "Cohesion in academic writing refers to the linguistic mechanisms that create textual continuity and coherence. These include reference, substitution, ellipsis, conjunction, and lexical cohesion. Halliday and Hasan's framework identifies five main types of cohesive ties."),
    ("scaffolding", "advanced",
     "What's the difference between 'which' and 'that' in relative clauses?",
     "Try this: remove the clause from the sentence. If the meaning changes, use 'that'. If it still makes sense, use 'which' with a comma. Test it on a sentence!",
     "'That' introduces defining relative clauses while 'which' introduces non-defining relative clauses. Non-defining clauses are set off by commas."),
    ("turn_taking", "advanced",
     "I need to give a presentation in English next week and I'm nervous.",
     "What's the topic? Let's practice your opening — that's the hardest part. Once you nail the first 30 seconds, the rest flows.",
     "Presentation anxiety in L2 speakers is multifaceted, involving linguistic anxiety, performance anxiety, and audience anxiety. Preparation strategies include script writing, rehearsal, visualization, and progressive exposure."),
    ("scaffolding", "advanced",
     "How do I use the passive voice effectively?",
     "When do you want to hide who did something, or when the action matters more than the actor? Give me a sentence and we'll decide together if passive works.",
     "The passive voice is formed with the auxiliary 'be' plus the past participle. It is used when the agent is unknown, unimportant, or when the speaker wishes to foreground the patient."),
    ("turn_taking", "advanced",
     "Can we discuss the differences between British and American English?",
     "Sure! Which aspect interests you most — pronunciation, spelling, or vocabulary? Pick one and we'll dive in.",
     "British and American English differ in numerous ways across all levels of linguistic analysis. In terms of phonology, there are differences in vowel quality, rhoticity, and stress patterns. Lexically, many everyday items have different names. Grammatically, there are differences in verb forms, preposition usage, and collective noun agreement. In terms of spelling, the most well-known differences include -our versus -or, -ise versus -ize, and -re versus -er."),
]

for dim, lvl, prompt, chosen, rejected in MULTI_TURN_ADVANCED:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Situational roleplay expansion (turn_taking, mixed levels) -------------
EXTRA_ROLEPLAYS = [
    ("beginner", "Let's practice buying a bus ticket.",
     "I'm the driver. You step on — what do you say first?",
     "Bus ticket purchasing in English-speaking countries involves a sequence of transactional speech acts. Let me first explain the vocabulary and phrases you'll need."),
    ("beginner", "Can we practice ordering pizza?",
     "Sure! I'll be the pizza person. Ring ring... Hello, Pizza Place, what can I get you?",
     "Pizza ordering involves several communicative steps. First, you need to know the vocabulary for pizza toppings, sizes, crust types, and delivery options."),
    ("intermediate", "I have a parent-teacher meeting tomorrow.",
     "Let's practice! I'll be the teacher. Start with why you're there — are you asking about grades or behavior?",
     "Parent-teacher conferences in English-speaking educational contexts follow specific interactional norms including greeting rituals, information exchange sequences, and closing routines."),
    ("intermediate", "I need to complain about noise from my neighbor.",
     "Tough one! Start friendly — maybe 'Hi, I wanted to talk about something.' What would you say next?",
     "Complaint speech acts in English require careful face management. Brown and Levinson's politeness theory suggests using negative politeness strategies to mitigate the face-threatening nature of complaints."),
    ("advanced", "Let's practice a salary negotiation.",
     "I'll be your boss. You've just been offered the job. Go — make your case!",
     "Salary negotiation in English involves complex pragmatic strategies including anchoring, justified counter-offers, framing effects, and strategic use of silence and hedging."),
    ("advanced", "I need to moderate a panel discussion at a conference.",
     "Great! Let's start with your opening. Introduce the topic and panelists — keep it under 30 seconds. Go!",
     "Panel moderation requires several discourse management skills including topic introduction, turn allocation, time management, audience engagement, and synthesis of panelist contributions."),
    ("beginner", "I'm going to the doctor. How do I describe pain?",
     "Key words: 'It hurts here' + point. 'Sharp pain' or 'dull ache'. Is it constant or does it come and go? Let's practice!",
     "Medical consultations require specific vocabulary including anatomical terms, symptom descriptors, duration markers, and intensity scales."),
    ("intermediate", "I need to return something to a store.",
     "I'll be the cashier. Walk in and tell me what's wrong with your item. Go!",
     "Product return interactions in retail contexts follow a predictable speech event structure including problem identification, reason presentation, and resolution negotiation."),
]

for lvl, prompt, chosen, rejected in EXTRA_ROLEPLAYS:
    pairs.append(("turn_taking", lvl, prompt, chosen, rejected))

# --- Listening and comprehension pairs (scaffolding, mixed) -----------------
COMPREHENSION_PAIRS = [
    ("beginner", "I don't understand when people speak fast.",
     "That's normal! Ask them to slow down: 'Could you speak more slowly, please?' No one minds. Want to practice that phrase?",
     "Processing speed limitations in L2 listening comprehension are attributable to insufficient automaticity in lexical access, working memory constraints, and inadequate phonological representations."),
    ("beginner", "What does 'gonna' mean?",
     "It's the fast way people say 'going to'. So 'I'm gonna eat' = 'I'm going to eat.' Listen for it in movies!",
     "'Gonna' is a reduced form of 'going to' that occurs through phonological processes of vowel reduction and consonant assimilation in casual connected speech."),
    ("intermediate", "I can read but I can't understand spoken English well.",
     "Your ears need practice catching sounds your eyes already know. Let's start — I'll say a sentence and you repeat what you hear.",
     "The gap between reading and listening skills indicates that your bottom-up processing needs development. Bottom-up processing involves phoneme recognition, word segmentation, and syntactic parsing of the acoustic signal."),
    ("intermediate", "Why do some words sound completely different when people actually say them?",
     "Because spoken English squishes words together! 'Did you eat yet?' becomes 'Jeet yet?' Let's practice a few of these common ones.",
     "This phenomenon is explained by connected speech processes including assimilation, where sounds change to become more like neighboring sounds; elision, where sounds are deleted; and catenation, where sounds link across word boundaries."),
    ("advanced", "How can I understand different English accents better?",
     "Expose yourself to variety — watch Scottish, Australian, Indian English content. Pick one accent this week. Which one trips you up most?",
     "Accent comprehension requires exposure to sociolinguistic variation across English varieties. Major accent differences involve vowel systems, consonant inventories, prosodic patterns, and lexical stress assignment."),
]

for lvl, prompt, chosen, rejected in COMPREHENSION_PAIRS:
    pairs.append(("scaffolding", lvl, prompt, chosen, rejected))

# --- Error correction for advanced learners --------------------------------
ADVANCED_ERRORS = [
    ("The reason is because he was late.",
     "Almost! 'The reason is because' is redundant — pick one. Either 'The reason is that he was late' or 'He was late because...' Which sounds better to you?",
     "'The reason is because' is a tautology. Use either 'The reason is that' or rephrase with 'because' alone."),
    ("I could care less about that.",
     "Interesting one! Think about it — if you COULD care less, that means you still care some. The phrase is 'I couldn't care less.' It's a common mix-up even for native speakers!",
     "The correct idiom is 'I couldn't care less.' 'I could care less' is a widespread error that is illogical."),
    ("For all intensive purposes, the project is done.",
     "The phrase is actually 'for all intents and purposes' — it just sounds like 'intensive purposes' when spoken fast. A classic one!",
     "'For all intensive purposes' is an eggcorn — a misheard version of 'for all intents and purposes.'"),
    ("He's been working here since five years.",
     "Close! 'Since' needs a point in time, like 'since 2019'. For a duration like 'five years', which word works?",
     "'Since' requires a point in time. 'For' is used with durations. Correct: 'He's been working here for five years.'"),
    ("Between you and I, she's going to resign.",
     "Good instinct to use 'I' — it sounds formal! But after prepositions like 'between', we use 'me'. So 'between you and me.' Try it!",
     "After prepositions, the objective case is required. 'Between you and I' is a hypercorrection. The correct form is 'between you and me.'"),
    ("I literally died of embarrassment.",
     "Ha! That word has shifted a lot. Technically 'literally' means it actually happened — and you're still here! In formal English, try 'I was mortified.' In casual speech, people use 'literally' for emphasis all the time now.",
     "'Literally' should only be used to indicate non-figurative meaning. Using it as an intensifier with figurative expressions is considered non-standard."),
    ("Irregardless, we should continue.",
     "People say this a lot! But 'regardless' already means 'without regard', so the 'ir-' is extra. Just 'regardless' works. Sounds smoother too!",
     "'Irregardless' is a non-standard form. The correct word is 'regardless.' The prefix 'ir-' creates a double negative with '-less.'"),
    ("She graduated college last year.",
     "In formal English, it's 'graduated from college' — that 'from' matters! In everyday American English, dropping it is common though. What's the context?",
     "'Graduate' is an intransitive verb that requires the preposition 'from.' The correct form is 'graduated from college.'"),
]

for wrong_sent, chosen, rejected in ADVANCED_ERRORS:
    pairs.append(("error_correction", "advanced", wrong_sent, chosen, rejected))

# --- Motivation and encouragement (turn_taking, mixed) ---------------------
MOTIVATION_PAIRS = [
    ("beginner", "I feel like I'm not improving.",
     "You are — you just can't see it yet! Tell me something you can say now that you couldn't a month ago.",
     "Language learning follows a non-linear trajectory. Perceived plateaus are often periods of restructuring in the interlanguage system where implicit knowledge is being consolidated."),
    ("beginner", "English is too hard. I want to quit.",
     "I hear you — it IS hard. But you're talking to me right now, in English! What part feels hardest?",
     "Language learning difficulty is influenced by factors including L1 transfer, motivation type, learning context, aptitude, and the psychotypological distance between L1 and L2."),
    ("intermediate", "I keep making the same mistakes over and over.",
     "That actually means you're close to fixing them — you notice them now! Which mistake bugs you the most?",
     "Persistent errors in interlanguage development may indicate fossilization, a phenomenon where certain non-target features become fixed despite continued input and instruction."),
    ("intermediate", "Everyone speaks better than me.",
     "Comparison is the thief of joy! They probably struggled too. What's one thing you've gotten better at recently?",
     "Social comparison in language learning contexts can increase affective filter and reduce willingness to communicate. Focus on individual progress metrics rather than peer comparison."),
    ("advanced", "I've hit a plateau. I can't seem to get better.",
     "At your level, growth is subtle — it's more about nuance than new rules. What specific situation makes you feel stuck?",
     "Advanced-level plateaus are characterized by the difficulty of moving from B2/C1 to C2 proficiency. Progress at this stage requires sustained exposure to varied registers, deliberate attention to collocational patterns, and metalinguistic awareness."),
]

for lvl, prompt, chosen, rejected in MOTIVATION_PAIRS:
    pairs.append(("turn_taking", lvl, prompt, chosen, rejected))

# --- Vocabulary in context (scaffolding, beginner+intermediate) ------------
VOCAB_IN_CONTEXT = [
    ("beginner", "What does 'appointment' mean?",
     "It's a planned meeting at a set time — like going to the doctor at 3 PM. Do you have any appointments this week?",
     "The meeting is at 3 PM."),
    ("beginner", "What is 'traffic'?",
     "Traffic is all the cars on the road. When there's a lot of traffic, you move slowly. Has that happened to you?",
     "'Traffic' refers to vehicles moving on a road."),
    ("beginner", "What does 'borrow' mean?",
     "When you take something and give it back later — like 'Can I borrow your pen?' The opposite is 'lend'. Try asking me to borrow something!",
     "'Borrow' means to take and use something belonging to someone else with the intention of returning it."),
    ("intermediate", "What does 'deadline' mean?",
     "It's the last moment you can finish something — after that, you're late! Do you have any deadlines soon?",
     "'Deadline' is a noun referring to the latest time or date by which something should be completed. Originally a military term."),
    ("intermediate", "What's the difference between 'trip', 'travel', and 'journey'?",
     "'Trip' is a short one — a day trip. 'Journey' is longer and about getting there. 'Travel' is the general activity. Which are you planning?",
     "'Trip' denotes a short excursion, 'travel' is the general activity of moving between places, and 'journey' emphasizes the process of traveling, often with connotations of length or significance."),
    ("intermediate", "What does 'get over' something mean?",
     "It means to recover from something bad — 'I got over my cold' or 'She got over the breakup.' What would you use it for?",
     "'Get over' is a phrasal verb meaning to recover from an illness, disappointment, or difficulty."),
    ("advanced", "What does 'nuance' mean?",
     "A subtle difference that matters. Like 'happy' vs 'content' — close but not the same. That difference is the nuance. Where have you heard it?",
     "'Nuance' refers to a subtle difference in meaning, expression, or response. It derives from the French word meaning 'shade.'"),
    ("advanced", "What's the difference between 'empathy' and 'sympathy'?",
     "Empathy = you feel what they feel. Sympathy = you feel sorry for them. One is 'I understand your pain', the other is 'I'm sorry you're in pain.' Big difference!",
     "'Empathy' involves vicariously experiencing another's emotional state, while 'sympathy' involves feeling compassion or pity for another's situation without necessarily sharing the emotional experience."),
]

for lvl, prompt, chosen, rejected in VOCAB_IN_CONTEXT:
    pairs.append(("scaffolding", lvl, prompt, chosen, rejected))

# ─── BATCH 2: MORE EXPANSION TEMPLATES (targeting 500+) ─────────────────────

# --- Tense confusion pairs (error_correction + scaffolding, mixed) ----------
TENSE_CONFUSIONS = [
    ("beginner", "I am living here since 2020.",
     "error_correction",
     "Good try! 'Since 2020' tells us it started in the past and continues now — that's present perfect. Try: 'I have lived here since 2020.'",
     "Wrong tense. Use present perfect with 'since'. Correct: 'I have lived here since 2020.'"),
    ("beginner", "Yesterday I have gone to the park.",
     "error_correction",
     "Close! 'Yesterday' is a finished time, so we use simple past — 'I went to the park.' 'Have gone' is for when the time isn't finished. Try it!",
     "Incorrect. 'Have gone' is present perfect and cannot be used with 'yesterday'. Say 'I went to the park.'"),
    ("intermediate", "I will call you when I will arrive.",
     "error_correction",
     "Almost perfect! In English, after 'when' we use present tense for future events. So: 'I will call you when I arrive.' Sounds odd but that's the rule!",
     "The second 'will' is wrong. After temporal conjunctions like 'when', use present simple for future reference."),
    ("intermediate", "By next year, I study English for five years.",
     "error_correction",
     "You need a tense that shows duration up to a future point. What tense combines 'will', 'have', and 'been'? Try: 'I will have been studying...'",
     "Use future perfect continuous: 'By next year, I will have been studying English for five years.'"),
    ("advanced", "I had been knowing her for years before we became friends.",
     "error_correction",
     "'Know' is a state verb — it resists the continuous form. Try 'I had known her for years...' — the past perfect simple works perfectly here.",
     "'Know' is a stative verb incompatible with progressive aspect. Correct: 'I had known her for years.'"),
    ("beginner", "I am eat breakfast now.",
     "error_correction",
     "You're using the right tense — present continuous! Just add '-ing' to the verb: 'I am eating breakfast now.' Try it!",
     "Wrong form. Present continuous requires be + verb-ing. Say 'I am eating breakfast now.'"),
    ("intermediate", "When I was young, I am playing outside every day.",
     "error_correction",
     "Good memory! But since it was a regular habit in the past, both verbs need past tense. Try: 'When I was young, I played outside every day.' Or even 'used to play'!",
     "Tense inconsistency. Both clauses refer to past time. Correct: 'When I was young, I played outside every day.'"),
    ("advanced", "I wish I didn't say that yesterday.",
     "error_correction",
     "For regrets about the past, 'wish' needs the past perfect. Try: 'I wish I hadn't said that yesterday.' Feel the difference?",
     "For past regrets, use 'wish' + past perfect. Correct: 'I wish I hadn't said that yesterday.'"),
]

for lvl, prompt, dim, chosen, rejected in TENSE_CONFUSIONS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Article errors (error_correction, beginner+intermediate) ---------------
ARTICLE_ERRORS = [
    ("beginner", "I want to be doctor.",
     "Almost! Jobs need 'a' before them — 'I want to be a doctor.' Same for 'a teacher', 'an engineer'. Try another job!",
     "'Doctor' requires an indefinite article. Say 'I want to be a doctor.'"),
    ("beginner", "She is best student in class.",
     "Nice compliment! With 'best' we always use 'the' — 'She is the best student in the class.' Superlatives love 'the'!",
     "Superlative adjectives require the definite article. Correct: 'She is the best student in the class.'"),
    ("beginner", "I like the dogs.",
     "If you mean dogs in general, drop the 'the' — just 'I like dogs.' We only use 'the' for specific ones. Which did you mean?",
     "Generic reference does not take the definite article. Say 'I like dogs' for the general meaning."),
    ("intermediate", "She plays the piano beautifully but hates the homework.",
     "Half right! Musical instruments get 'the' — 'the piano' is perfect. But 'homework' is general, so no 'the'. 'She plays the piano but hates homework.'",
     "Musical instruments take the definite article but abstract/uncountable nouns in generic use do not."),
    ("intermediate", "I went to the bed early last night.",
     "We say 'go to bed' without 'the' — it's about the activity of sleeping, not the furniture. Same with 'go to school', 'go to work'. Try another one!",
     "'Go to bed' is a fixed expression without an article because it refers to the function, not the physical object."),
    ("advanced", "The life is short.",
     "In English, abstract concepts like 'life' don't take 'the' when you mean life in general. Just 'Life is short.' But 'The life of a sailor is tough' works because it's specific!",
     "Abstract nouns in generic reference do not take the definite article. Correct: 'Life is short.'"),
]

for lvl, prompt, chosen, rejected in ARTICLE_ERRORS:
    pairs.append(("error_correction", lvl, prompt, chosen, rejected))

# --- Word order / sentence structure (scaffolding, mixed) -------------------
WORD_ORDER_PAIRS = [
    ("beginner", "How do I make a negative sentence?",
     "scaffolding",
     "Start with what you know — 'I like pizza.' Now, to make it negative, where would you put 'don't'? Before or after the verb?",
     "Add 'do not' or 'don't' before the main verb. For 'be', add 'not' after it. For example: 'I don't like pizza' or 'I am not happy.'"),
    ("beginner", "How do I ask 'where' questions?",
     "scaffolding",
     "Start with 'where', then flip the subject and verb. 'You are' becomes 'Where are you?' Now try: 'The bathroom is' — make it a question!",
     "Wh-questions are formed by placing the wh-word at the beginning, followed by subject-auxiliary inversion."),
    ("intermediate", "How do I use 'not only... but also'?",
     "scaffolding",
     "It's for emphasis — linking two impressive things. 'She not only speaks English but also writes poetry.' What two things would you link about yourself?",
     "'Not only... but also' is a correlative conjunction pair used for additive emphasis. The second element may optionally include 'also.'"),
    ("intermediate", "How do I report what someone said?",
     "scaffolding",
     "Change the tense one step back — 'I am happy' becomes 'She said she was happy.' Try converting: 'I will come tomorrow.'",
     "Reported speech involves backshifting tenses, changing pronouns, and adjusting time/place references."),
    ("advanced", "How does inversion work after negative adverbs?",
     "scaffolding",
     "Put the negative word first, then flip subject and auxiliary — like a question. 'Never have I seen...' instead of 'I have never seen...' Try one with 'rarely'.",
     "Negative inversion places the negative adverb in sentence-initial position and triggers subject-auxiliary inversion."),
    ("advanced", "How do I use cleft sentences for emphasis?",
     "scaffolding",
     "Take a normal sentence: 'John broke the window.' What part do you want to emphasize? If it's John: 'It was John who broke the window.' Try emphasizing 'the window'.",
     "Cleft sentences use the structure 'It + be + focused element + relative clause' to foreground specific information."),
]

for lvl, prompt, dim, chosen, rejected in WORD_ORDER_PAIRS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Daily situations (difficulty_calibration, mixed) -----------------------
DAILY_SITUATIONS = [
    ("beginner", "How do I ask for the bathroom?",
     "'Excuse me, where is the bathroom?' — simple and polite! In formal places you can say 'restroom'. Want to practice asking?",
     "Locative interrogatives for sanitation facilities vary by dialect: 'bathroom' in American English, 'toilet' or 'loo' in British English, 'washroom' in Canadian English."),
    ("beginner", "How do I tell the taxi driver where I want to go?",
     "Say the place name and add 'please' — 'Central Station, please.' If they don't know it, try the street address. Let's practice!",
     "Taxi directives require locative specifications using either proper nouns, street addresses with cardinal directions, or relative spatial descriptions."),
    ("beginner", "How do I say I don't understand?",
     "'I don't understand' or 'Sorry, could you repeat that?' Both are perfectly fine. Which feels easier to remember?",
     "Comprehension failure signals in English include both direct ('I don't understand') and indirect strategies (clarification requests, confirmation checks, and comprehension checks)."),
    ("intermediate", "How do I make small talk at a party?",
     "Ask about how they know the host, what they do, or comment on the food. 'Great party, right?' is always a safe start. What's your biggest worry?",
     "Party small talk follows specific interactional norms involving topic initiation, maintenance, and transition across multiple conversational sequences."),
    ("intermediate", "How do I apologize properly in English?",
     "'I'm sorry about...' + what happened. Then say what you'll do differently. 'I'm sorry I was late — I'll leave earlier next time.' What's the situation?",
     "Apologies in English involve multiple speech act components including an expression of regret, acknowledgment of responsibility, an offer of repair, and a promise of non-recurrence."),
    ("intermediate", "How do I ask someone to repeat something without sounding rude?",
     "'Sorry, could you say that again?' or 'I didn't quite catch that' — both are polite. 'What?' by itself sounds rude. Try one!",
     "Repair initiators in English conversation range from open class ('What?') to more specific strategies including partial repeats, candidate understandings, and metalinguistic requests."),
    ("advanced", "How do I give constructive feedback to a colleague in English?",
     "Start with what's working: 'I really liked X.' Then: 'One thing that could be even better is...' Soften with 'might' and 'perhaps'. What's the situation?",
     "Constructive feedback in professional English contexts requires careful face management using hedging, positive politeness strategies, and the sandwich technique."),
    ("advanced", "How do I chair a meeting effectively in English?",
     "Open with 'Let's get started. Today we're covering...' Keep people on track with 'Let's circle back to that' and close with 'To sum up...' What kind of meeting?",
     "Meeting facilitation requires mastery of discourse management functions including agenda setting, turn allocation, topic management, and summarization."),
    ("beginner", "How do I count money in English?",
     "For coins: penny, nickel, dime, quarter. For bills: one dollar, five dollars, ten... Let's practice! If something costs $3.50, how would you say it?",
     "English monetary denomination involves base-10 counting with specific lexemes for coinage that vary by national variety."),
    ("beginner", "How do I tell the time?",
     "For 3:00 say 'three o'clock'. For 3:15 say 'quarter past three'. For 3:30 say 'half past three'. What time is it now? Try telling me!",
     "Time-telling in English follows an analogue or digital format. Analogue uses fractional expressions ('quarter past', 'half past') while digital is sequential ('three fifteen')."),
    ("intermediate", "How do I describe symptoms to a pharmacist?",
     "'I have a headache and a runny nose' — describe what you feel. Key words: ache, pain, fever, cough, dizzy. What's wrong? Let's practice!",
     "Symptom description in pharmaceutical encounters requires specific medical register including anatomical vocabulary, symptom descriptors, and temporal markers."),
    ("advanced", "How do I write a cover letter?",
     "First paragraph: why you're writing. Second: what you bring. Third: why this company. End: 'I look forward to hearing from you.' What job is it for?",
     "Cover letter composition follows genre conventions including an opening move establishing the applicant's purpose, a credentials move establishing qualifications, and a closing move requesting action."),
]

for lvl, prompt, chosen, rejected in DAILY_SITUATIONS:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Collocations and natural phrasing (verbosity, intermediate+advanced) ---
COLLOCATION_PAIRS = [
    ("intermediate", "What does 'make a decision' mean? Why not 'do a decision'?",
     "In English, certain verbs go with certain nouns — we 'make' decisions, 'do' homework, 'take' a shower. It's like word friendships. Can you guess: do we 'make' or 'do' a mistake?",
     "This is a collocation — a conventionalized word combination. English has two main delexical verbs for general activity: 'make' and 'do'. 'Make' tends to collocate with nouns denoting creation or production while 'do' collocates with nouns denoting tasks or activities."),
    ("intermediate", "Why do we say 'heavy rain' not 'strong rain'?",
     "Good catch! It's just how English pairs words. We say 'heavy rain' but 'strong wind'. These combos are called collocations. Try this: is coffee 'strong' or 'heavy'?",
     "This is a collocational restriction. 'Heavy' collocates with 'rain', 'traffic', and 'snow' while 'strong' collocates with 'wind', 'coffee', and 'opinion'. These pairings are arbitrary and must be learned individually."),
    ("advanced", "How do I stop sounding like a textbook when I speak?",
     "Use more phrasal verbs! Swap 'discover' for 'find out', 'tolerate' for 'put up with'. Also, add filler words like 'well', 'I mean'. Try converting: 'I must depart now.'",
     "Register shifting from formal written to informal spoken English involves lexical simplification, increased use of phrasal verbs, deployment of discourse markers, and phonological reduction."),
    ("advanced", "What are some good transition words for essays?",
     "'However' for contrast, 'moreover' to add, 'consequently' for result, 'nevertheless' for surprise. Pick one and use it in a sentence about your topic.",
     "Transition words in academic writing serve as metadiscoursal markers. They can be categorized by function: additive (furthermore, moreover), adversative (however, nevertheless), causal (consequently, therefore), and sequential (firstly, subsequently)."),
    ("intermediate", "Why do we say 'by accident' but 'on purpose'?",
     "English prepositions are weird like that — there's often no logic, just tradition. 'By' for accidents, 'on' for intentions. You just have to memorize the pairs. Try using both in a sentence!",
     "Prepositional collocations in English are largely arbitrary and cannot be predicted by rule. They must be learned as fixed chunks."),
    ("intermediate", "What does 'catch a cold' mean? You can't really catch it!",
     "Ha, exactly! It just means to get sick with a cold. We also 'catch' a bus, 'catch' someone's eye, and 'catch' a break. English is creative with 'catch'!",
     "'Catch a cold' is a delexicalized collocation where 'catch' does not carry its core meaning of physical grasping."),
]

for lvl, prompt, chosen, rejected in COLLOCATION_PAIRS:
    pairs.append(("verbosity", lvl, prompt, chosen, rejected))

# --- Grammar explanation pairs (scaffolding, mixed) -------------------------
GRAMMAR_EXPLANATION = [
    ("beginner", "What is 'the' for?",
     "'The' points to something specific. 'A cat' is any cat. 'The cat' is one we both know about. If I say 'the door' — which door? The one near us!",
     "The definite article 'the' is used for specific reference when the referent is identifiable."),
    ("beginner", "When do I use 'is' and when 'are'?",
     "'Is' goes with one thing — 'the cat is sleeping.' 'Are' goes with more than one — 'the cats are sleeping.' Try: 'My friends ___ here.'",
     "'Is' is used with singular subjects and 'are' with plural subjects in subject-verb agreement."),
    ("beginner", "What are prepositions?",
     "They show where or when — 'in the box', 'on the table', 'at 3 o'clock'. Try: where is your phone right now? Use 'in', 'on', or 'under'!",
     "Prepositions are function words that express spatial, temporal, or logical relationships between constituents."),
    ("intermediate", "When do I use present perfect vs simple past?",
     "Simple past = finished, done. Present perfect = connected to now. 'I ate lunch' (done). 'I've eaten lunch' (so I'm not hungry now). The present matters! Try one.",
     "Present perfect connects past events to the present; simple past refers to completed events at a definite past time."),
    ("intermediate", "What are modal verbs?",
     "Words like 'can', 'should', 'must', 'might' — they add meaning to the main verb. 'I swim' vs 'I can swim' vs 'I must swim'. Feel the difference? Which one shows ability?",
     "Modal verbs are auxiliary verbs that express modality — possibility, necessity, permission, obligation, and ability."),
    ("advanced", "How do I use the subjunctive in English?",
     "It's rare but appears in formal English — 'I suggest that he be present' not 'he is present'. Also after 'if I were you'. Can you spot what's unusual about those?",
     "The subjunctive mood in English is used for counterfactuals, wishes, and mandative contexts."),
    ("advanced", "What's the difference between 'used to' and 'would' for past habits?",
     "'Used to' works for habits AND states — 'I used to live there.' 'Would' only works for repeated actions — 'I would visit every summer.' You can't say 'I would live there.' Try both!",
     "'Used to' marks both past habitual actions and past states. 'Would' only marks past habitual actions, not states."),
]

for lvl, prompt, chosen, rejected in GRAMMAR_EXPLANATION:
    pairs.append(("scaffolding", lvl, prompt, chosen, rejected))

# --- Technology and modern English (difficulty_calibration, mixed) ----------
MODERN_ENGLISH = [
    ("beginner", "What does 'selfie' mean?",
     "It's a photo you take of yourself — usually with your phone. Do you take selfies?",
     "'Selfie' is a neologism formed by the productive English suffix '-ie/-y' denoting familiarity. It entered mainstream usage circa 2013 and was Oxford Dictionaries' Word of the Year."),
    ("beginner", "What does 'Google it' mean?",
     "It means to search for something on the internet — 'I don't know, let me Google it.' The company name became a verb! What would you Google?",
     "'Google' has undergone conversion from a proper noun to a verb through a process called anthimeria, similar to 'Xerox' and 'Hoover.'"),
    ("intermediate", "What does 'ghosting' mean?",
     "When someone suddenly stops replying to your messages without explanation. Has it happened to you? It's a new word but very common now.",
     "'Ghosting' is a digital-age neologism describing the practice of unilaterally and abruptly ceasing all communication with a person."),
    ("intermediate", "What is 'binge-watching'?",
     "Watching many episodes of a show in one sitting — like watching a whole season in a weekend! Do you binge-watch anything?",
     "'Binge-watching' is a compound verb formed from 'binge' (originally associated with excessive eating/drinking) and 'watching', reflecting contemporary media consumption patterns."),
    ("advanced", "What does 'virtue signaling' mean?",
     "It's when someone publicly expresses moral values mainly to look good, not necessarily because they act on them. It's often used critically. Where did you hear it?",
     "'Virtue signaling' is a pejorative neologism referring to the conspicuous expression of moral values primarily for social capital rather than genuine commitment."),
    ("advanced", "What's the difference between 'literally' and 'figuratively' in modern usage?",
     "Technically they're opposites! But nowadays people use 'literally' for emphasis even when they mean figuratively — 'I literally died laughing.' Purists hate it, but language evolves!",
     "The semantic bleaching of 'literally' represents a diachronic shift from its original denotative function to an intensifier, a process documented across many languages."),
]

for lvl, prompt, chosen, rejected in MODERN_ENGLISH:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Additional turn-taking for all levels ---------------------------------
EXTRA_TURN_TAKING = [
    ("beginner", "turn_taking",
     "I'm confused now.",
     "That's okay! Which part is confusing — the word or the grammar? Let's go back to that.",
     "Confusion is a natural part of the learning process. Research shows that productive confusion can actually enhance learning when it is resolved through appropriate scaffolding and support. Let me re-explain everything from the beginning."),
    ("beginner", "turn_taking",
     "Can you say that again?",
     "Of course! [Repeats simply.] Does that make more sense now?",
     "Certainly! Repetition is a fundamental learning strategy. I will now repeat the previous explanation, but let me also add some additional context and examples to ensure thorough understanding. The key points were as follows..."),
    ("beginner", "turn_taking",
     "Wait, I have a question.",
     "Go ahead! What's on your mind?",
     "Of course! Questions are a vital part of the learning process. They indicate active engagement with the material and demonstrate cognitive processing. Please feel free to ask any question at any time during our session."),
    ("intermediate", "turn_taking",
     "I think I need more practice with this.",
     "Absolutely. Let's do three quick exercises — I'll give you a prompt and you respond. Ready?",
     "Practice is indeed essential for language acquisition. Research in applied linguistics has consistently demonstrated that repeated practice, particularly spaced practice, leads to better retention and automaticity. There are several types of practice we can do: controlled practice, free practice, communicative practice, and task-based practice."),
    ("intermediate", "turn_taking",
     "That's helpful, thanks!",
     "Glad to hear it! Want to try a harder version or move to something new?",
     "You're welcome! I'm glad you found that helpful. Language learning is a journey and every small step counts. There are many more aspects of this topic we could explore if you're interested. We've covered the basics but there are also advanced uses, exceptions, and related structures that might be useful for you."),
    ("intermediate", "turn_taking",
     "I made that mistake again!",
     "Progress isn't linear — the fact you noticed means you're getting better. Say it again, correctly this time.",
     "Making repeated errors is completely normal in the language learning process. Interlanguage theory, developed by Larry Selinker in 1972, explains that learners create a transitional linguistic system that has features of both their first and target languages."),
    ("advanced", "turn_taking",
     "I disagree with that grammar rule.",
     "Interesting — tell me why! Language does evolve, and some 'rules' are debatable.",
     "Your disagreement raises an important point about prescriptivism versus descriptivism in linguistics. Prescriptive grammar dictates what speakers should say based on traditional norms, while descriptive grammar documents what speakers actually say. The tension between these approaches has been a central debate in linguistics since the 18th century."),
    ("advanced", "turn_taking",
     "Can you explain that differently? Your first explanation didn't click.",
     "Sure! Let me try an analogy instead. Think of it like this...",
     "I apologize if my initial explanation was unclear. Let me provide a more comprehensive explanation that covers all the relevant aspects of this topic from multiple angles, including the theoretical foundations, practical applications, common exceptions, and historical development."),
    ("beginner", "turn_taking",
     "You're going too fast.",
     "Sorry about that! Let's slow down. One thing at a time. What's the last part you understood?",
     "I apologize for the pace. Let me adjust. Pacing is an important factor in language instruction. Krashen's input hypothesis suggests that comprehensible input, slightly above the learner's current level, is optimal for acquisition."),
    ("intermediate", "turn_taking",
     "Can we take a break? My brain is full.",
     "Ha, of course! Come back when you're ready. You did great today.",
     "Mental fatigue during language learning is a well-documented phenomenon. Cognitive load theory suggests that working memory has limited capacity, and when that capacity is exceeded, learning efficiency decreases. It's important to take regular breaks to allow for memory consolidation."),
    ("advanced", "turn_taking",
     "That explanation was perfect. Now I want to see it in real context.",
     "Great instinct! Here's a paragraph from a news article — can you spot the pattern we just discussed?",
     "Excellent! Contextual application is crucial for moving from declarative to procedural knowledge. Let me first outline the different types of contexts where this structure appears: academic writing, journalism, fiction, business communication, and casual speech each present unique patterns of usage."),
    ("beginner", "turn_taking",
     "I forgot what we learned last time.",
     "No worries — that happens! Let's do a quick review. The main thing was... Do you remember any of it?",
     "Forgetting is a natural process governed by Ebbinghaus's forgetting curve, which shows that memory retention decays exponentially over time without reinforcement. Spaced repetition systems can help mitigate this decay by scheduling reviews at optimal intervals."),
]

for lvl, dim, prompt, chosen, rejected in EXTRA_TURN_TAKING:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Additional difficulty calibration pairs --------------------------------
EXTRA_CALIBRATION = [
    ("beginner", "I learned English in school but forgot everything.",
     "No problem — it'll come back fast! Let's start with introductions. Tell me your name and one thing you like.",
     "Let's assess your residual L2 competence across phonological, morphosyntactic, and lexical domains to determine your placement on the CEFR scale."),
    ("beginner", "I only speak English at work for simple things.",
     "That's actually great practice! What phrases do you use most at work? Let's build from there.",
     "Workplace English for limited proficiency speakers typically involves formulaic sequences, transactional language, and domain-specific vocabulary."),
    ("intermediate", "I can have conversations but my grammar is messy.",
     "That's actually a good sign — you're communicating! Let's clean up one grammar point at a time. What error do people correct most?",
     "The fluency-accuracy trade-off is a well-known phenomenon in second language acquisition. Your communicative competence has outpaced your linguistic competence."),
    ("intermediate", "I need to pass the TOEFL exam.",
     "When's the test? Let's focus on the section you find hardest. Is it reading, listening, speaking, or writing?",
     "TOEFL iBT assesses four communicative competencies across a range of task types designed to measure academic English proficiency."),
    ("advanced", "I can write well but my spoken English is weaker.",
     "Common for advanced learners! Speaking needs speed that writing doesn't. Let's practice thinking aloud — describe what you see around you, right now. Go!",
     "The discrepancy between written and oral proficiency at advanced levels often reflects differences in processing demands, planning time, and monitoring capacity."),
    ("advanced", "I want to learn how to tell jokes in English.",
     "Humor is the final frontier! It's all about timing and wordplay. Here's a simple one: 'Why don't scientists trust atoms? Because they make up everything.' Get it? 'Make up' has two meanings!",
     "Humor competence in a second language requires mastery of ambiguity resolution, cultural schema, pragmatic inferencing, and prosodic delivery."),
    ("beginner", "My child speaks English better than me. It's embarrassing.",
     "Kids pick up languages differently — it doesn't mean you can't! You actually have advantages they don't — like understanding grammar rules. What do you want to learn first?",
     "Age-related differences in language acquisition are explained by the Critical Period Hypothesis, though its validity remains debated in applied linguistics."),
    ("intermediate", "I understand British English but not American English.",
     "They're more alike than different! The main gaps are vocabulary — 'flat' vs 'apartment', 'boot' vs 'trunk'. Want me to list the most common differences?",
     "Dialectal comprehension difficulties between British and American English varieties stem from phonological, lexical, and occasionally syntactic differences."),
    ("advanced", "I need to give a TED-style talk in English.",
     "Exciting! The key is: one idea, personal stories, and a clear structure. What's your core message in one sentence?",
     "TED-style presentations follow a rhetorical structure involving a hook, narrative arc, key insight, and call to action, all delivered within a constrained temporal frame."),
    ("beginner", "How do I learn English fast?",
     "Practice a little every day — even 10 minutes! Talk to yourself in English, watch shows, and don't be afraid of mistakes. What's your biggest challenge right now?",
     "Second language acquisition rate is influenced by multiple variables including L1 transfer, aptitude, motivation, input quality, output opportunities, and explicit instruction."),
]

for lvl, prompt, chosen, rejected in EXTRA_CALIBRATION:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Spelling and writing mechanics (error_correction, beginner+intermediate)
SPELLING_PAIRS = [
    ("beginner", "Is it 'their', 'there', or 'they're'?",
     "'Their' = belonging to them. 'There' = a place. 'They're' = they are. Try: '___ going to ___ house over ___.'",
     "These are homophones: 'their' is a possessive determiner, 'there' is a locative adverb, and 'they're' is a contraction."),
    ("beginner", "What's the difference between 'your' and 'you're'?",
     "'Your' = belonging to you. 'You're' = you are. Quick test: if you can say 'you are', use 'you're'. 'You're nice' works. 'Your book' — can you say 'you are book'? No!",
     "'Your' is a possessive determiner. 'You're' is a contraction of 'you are'. They are frequently confused homophones."),
    ("intermediate", "When do I use 'its' vs 'it's'?",
     "'It's' always means 'it is' or 'it has'. 'Its' shows ownership. 'It's a dog. Its tail is wagging.' The apostrophe = contraction, not possession here!",
     "'Its' is the possessive form of 'it'. 'It's' is a contraction. This is counterintuitive because possessives usually use apostrophes."),
    ("intermediate", "How do I use semicolons?",
     "A semicolon joins two related complete sentences. 'I love English; it's a fun language.' Both sides must be full sentences. Try one!",
     "The semicolon is used between independent clauses that are closely related in meaning but not joined by a coordinating conjunction."),
    ("advanced", "When should I use a dash versus a comma?",
     "A dash adds drama or surprise — like this! A comma is quieter, more routine. 'He finally arrived — three hours late' hits different than 'He finally arrived, three hours late.'",
     "The em dash serves as a versatile punctuation mark that can replace commas, parentheses, or colons. It signals a sharper break than a comma."),
]

for lvl, prompt, chosen, rejected in SPELLING_PAIRS:
    pairs.append(("error_correction", lvl, prompt, chosen, rejected))

# ─── BATCH 3: FINAL PUSH TO 500+ ────────────────────────────────────────────

# --- Workplace English (turn_taking + verbosity, intermediate+advanced) -----
WORKPLACE_PAIRS = [
    ("turn_taking", "intermediate",
     "How do I ask my boss for a day off?",
     "Keep it simple: 'Would it be possible to take next Friday off?' What's the reason — you don't have to share it, but it helps to practice the full conversation.",
     "Requesting time off in professional English involves specific pragmatic strategies including pre-request sequences, justification moves, hedging, and conditional constructions to mitigate the face-threatening nature of the request."),
    ("turn_taking", "intermediate",
     "My coworker keeps interrupting me in meetings.",
     "Frustrating! Try: 'Could I finish my point?' or raise your hand slightly. Want to practice some assertive phrases?",
     "Turn-taking violations in institutional discourse can be addressed through both verbal and non-verbal repair strategies. Verbal strategies include explicit meta-communicative statements and indirect speech acts."),
    ("turn_taking", "advanced",
     "How do I present bad news to a client?",
     "Lead with context, then the news, then the solution. 'I wanted to update you — we've hit a delay, but here's our plan.' What's the situation?",
     "Delivering negative information in professional contexts requires careful face management through various discourse strategies including pre-announcements, hedging, account-giving, and remedial offerings."),
    ("verbosity", "intermediate",
     "What does 'touch base' mean in business English?",
     "It means to briefly check in with someone — 'Let me touch base with you tomorrow about the project.' Quick and casual.",
     "'Touch base' is a business English idiom derived from baseball terminology. It means to make brief contact or communication, typically to exchange information or coordinate activities."),
    ("verbosity", "intermediate",
     "What does 'circle back' mean?",
     "It means to return to a topic later — 'Let's circle back to this after lunch.' Very common in meetings!",
     "'Circle back' is a contemporary business English phrasal verb meaning to revisit or return to a topic, issue, or person at a later point. It has become increasingly prevalent in corporate discourse."),
    ("verbosity", "advanced",
     "What does 'move the needle' mean?",
     "It means to make noticeable progress — like a gauge needle moving. 'Will this campaign move the needle on sales?' Something that has real impact.",
     "'Move the needle' is a metaphorical business expression derived from the analog gauge metaphor, meaning to make a measurable or significant difference in a metric or outcome."),
    ("turn_taking", "advanced",
     "How do I give a status update in a standup meeting?",
     "Three things: what you did yesterday, what you're doing today, and any blockers. Keep each under 30 seconds. Try it now!",
     "Standup meeting contributions follow a formulaic three-part structure: retrospective report, prospective plan, and impediment identification, all delivered within strict temporal constraints."),
    ("verbosity", "advanced",
     "What's the difference between 'ROI' and 'KPI'?",
     "ROI = Return on Investment — did you make more than you spent? KPI = Key Performance Indicator — a metric you track. ROI can be one of your KPIs!",
     "ROI (Return on Investment) is a financial metric calculated as (net profit / cost of investment) × 100. KPI (Key Performance Indicator) is a quantifiable measure used to evaluate success in meeting objectives."),
]

for dim, lvl, prompt, chosen, rejected in WORKPLACE_PAIRS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Social English and politeness (turn_taking + difficulty_calibration) ---
SOCIAL_PAIRS = [
    ("turn_taking", "beginner",
     "How do I say no to an invitation politely?",
     "'Thanks for inviting me, but I can't make it' is perfect. You don't even need a reason! Want to practice a few ways?",
     "Declining invitations in English requires indirect speech acts that balance the competing demands of negative face (autonomy) and positive face (approval). Strategies include expressing gratitude, providing accounts, and offering alternatives."),
    ("turn_taking", "beginner",
     "How do I introduce two people to each other?",
     "'Maria, this is John. John, Maria.' Easy! For formal: 'I'd like you to meet...' Want to try?",
     "Social introductions in English follow specific sequential conventions. The person of lower status is typically introduced to the person of higher status first."),
    ("difficulty_calibration", "beginner",
     "How do I say goodbye to a friend?",
     "'Bye!' or 'See you later!' For closer friends: 'Take care!' or 'Catch you later!' Which one do you like?",
     "Leave-taking sequences in English involve pre-closing signals, terminal exchanges, and post-terminal elements. Common farewell formulae vary along dimensions of formality and intimacy."),
    ("difficulty_calibration", "intermediate",
     "How do I congratulate someone?",
     "'Congratulations!' is always safe. For something big: 'That's amazing, well done!' For casual: 'Nice one!' What's the occasion?",
     "Congratulatory speech acts in English vary across registers from formulaic ('Congratulations') to creative assessments, depending on the illocutionary force desired by the speaker."),
    ("difficulty_calibration", "advanced",
     "How do I express condolences in English?",
     "'I'm so sorry for your loss' is the standard. You can add: 'If there's anything I can do, please let me know.' Keep it sincere and short — less is more here.",
     "Condolence expressions in English are formulaic speech acts that draw on a limited set of conventional phrases, governed by cultural norms regarding emotional display and relational obligations."),
    ("turn_taking", "intermediate",
     "How do I ask someone to speak louder?",
     "'Sorry, could you speak up a bit?' or 'I can't quite hear you.' Both are polite. In a noisy place, lean closer and say 'Sorry?'",
     "Volume-related repair initiators in English include both specific ('Could you speak louder?') and non-specific ('Sorry?') forms, often accompanied by paralinguistic cues."),
    ("difficulty_calibration", "beginner",
     "How do I say 'I don't know' politely?",
     "'I'm not sure' sounds softer than 'I don't know.' You can also say 'Good question — let me think about it.' Try one!",
     "Epistemic hedging strategies in English include modal verbs, adverbs of uncertainty, and formulaic expressions that mitigate the face-threatening implications of knowledge gaps."),
    ("turn_taking", "advanced",
     "How do I steer a conversation back on topic?",
     "'That's interesting — and speaking of that, I wanted to ask about...' or just 'So, going back to...' It's direct but works. Try one!",
     "Topic management in conversation involves complex discourse strategies including bridging, pivoting, and explicit meta-discoursal signals."),
]

for dim, lvl, prompt, chosen, rejected in SOCIAL_PAIRS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Reading and media (scaffolding + verbosity, mixed) ---------------------
MEDIA_PAIRS = [
    ("scaffolding", "beginner",
     "How do I read an English menu at a restaurant?",
     "Look for sections: starters, mains, desserts, drinks. Point at something and ask 'What is this?' — waiters are used to it! What kind of food do you like?",
     "Restaurant menus are organized by course categories. Scan for the relevant section."),
    ("scaffolding", "intermediate",
     "How do I understand English news headlines?",
     "Headlines drop small words — 'President Meets King' means 'The President Met the King.' They use present tense for past events too. Try decoding this: 'Stocks Soar Amid Rate Cut.'",
     "News headlines use a specific register called headlinese, characterized by noun stacking, article deletion, and present tense for past events."),
    ("verbosity", "beginner",
     "What does 'take a break' mean?",
     "It means to stop and rest for a while. 'Let's take a break' = let's pause and relax for a bit.",
     "'Take a break' is a phrasal expression meaning to temporarily cease an activity for the purpose of rest or refreshment."),
    ("verbosity", "intermediate",
     "What does 'sleep on it' mean?",
     "Wait until tomorrow before deciding — your mind works on problems while you sleep! 'Don't decide now, sleep on it.'",
     "'Sleep on it' is an idiomatic expression advising postponement of a decision until the following day, based on the cognitive benefits of an overnight incubation period."),
    ("scaffolding", "advanced",
     "How do I analyze tone in English literature?",
     "Look at word choice — is the author using dark or light words? Formal or casual? Try reading a paragraph aloud — how does it make you FEEL? That's the tone.",
     "Tone analysis requires examination of lexical choice, syntactic patterns, figurative language, and authorial stance."),
    ("verbosity", "advanced",
     "What does 'double-edged sword' mean?",
     "Something that has both good and bad effects. 'Social media is a double-edged sword — great for connecting, terrible for focus.' Both sides cut!",
     "A 'double-edged sword' is a metaphorical expression denoting something that has both advantageous and disadvantageous consequences simultaneously."),
]

for dim, lvl, prompt, chosen, rejected in MEDIA_PAIRS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Pronunciation minimal pairs (difficulty_calibration, beginner+intermediate)
MINIMAL_PAIRS = [
    ("beginner", "I can't hear the difference between 'ship' and 'sheep'.",
     "'Ship' is short — /ɪ/. 'Sheep' is long — /iː/. Try holding the 'ee' sound: sheeeeep. Now cut it short: ship. Hear it?",
     "These words form a minimal pair distinguished by the vowels /ɪ/ (near-close near-front unrounded) and /iː/ (close front unrounded), a phonemic contrast absent in many L1 systems."),
    ("beginner", "Is 'bed' and 'bad' the same sound?",
     "Not quite! 'Bed' has an 'e' sound — your mouth is smaller. 'Bad' has an 'a' sound — your mouth opens wider. Try saying them one after another!",
     "These words are distinguished by the vowels /e/ and /æ/, which differ in tongue height and mouth aperture."),
    ("intermediate", "I confuse 'three' and 'tree'.",
     "'Three' starts with your tongue between your teeth — feel the air? 'Tree' starts with your tongue behind your teeth. Exaggerate the difference first, then speed up.",
     "The distinction is between the voiceless dental fricative /θ/ and the voiceless alveolar stop /t/, differing in manner and place of articulation."),
    ("intermediate", "People don't understand when I say 'very' — they think I'm saying 'berry'.",
     "The key is your bottom lip! For 'v', your top teeth touch your bottom lip. For 'b', both lips close. Try: touch your lip with your teeth and say 'vvvvvery.'",
     "This is a /v/-/b/ confusion stemming from the neutralization of the labiodental fricative and bilabial stop contrast in your L1 phonological system."),
    ("beginner", "How do I pronounce 'ough' words? They all sound different!",
     "English spelling is wild! 'Though' = OH, 'through' = OO, 'tough' = UFF, 'cough' = OFF. They just have to be memorized. Let's practice the four most common ones.",
     "The 'ough' letter sequence has multiple phonological realizations due to historical sound changes that were not reflected in spelling reform."),
]

for lvl, prompt, chosen, rejected in MINIMAL_PAIRS:
    pairs.append(("difficulty_calibration", lvl, prompt, chosen, rejected))

# --- Error correction expansion (mixed levels) -----------------------------
MORE_ERRORS = [
    ("error_correction", "beginner",
     "Me and my friend went shopping.",
     "People say this all the time! Technically, it's 'My friend and I' when you're the subject. Trick: remove 'my friend and' — would you say 'Me went shopping'? That tells you!",
     "'Me and my friend' is incorrect as a subject. The nominative form 'My friend and I' is required."),
    ("error_correction", "beginner",
     "I have a new informations for you.",
     "Almost! 'Information' is one of those words that doesn't become plural — like 'water' or 'advice'. Just 'I have new information for you.' No 'a', no 's'!",
     "'Information' is an uncountable noun. It cannot take the indefinite article or a plural marker."),
    ("error_correction", "intermediate",
     "Can you borrow me your pen?",
     "Close! The directions are: you BORROW from someone, you LEND to someone. So: 'Can you lend me your pen?' or 'Can I borrow your pen?' Which feels right?",
     "'Borrow' and 'lend' are converses. 'Borrow' takes 'from'; 'lend' takes an indirect object. Correct: 'Can you lend me your pen?'"),
    ("error_correction", "intermediate",
     "I am interesting in this topic.",
     "So close! '-ing' describes the thing causing the feeling. '-ed' describes who feels it. The topic is interestING, but you are interestED. 'I am interested in this topic.'",
     "Participial adjectives ending in -ing describe the stimulus; those ending in -ed describe the experiencer. Correct: 'I am interested in this topic.'"),
    ("error_correction", "advanced",
     "The amount of people at the concert was huge.",
     "'Amount' goes with uncountable things — money, time, water. For countable things like people, use 'number'. 'The number of people...' Feel the difference?",
     "'Amount' collocates with uncountable nouns; 'number' with countable nouns. Correct: 'The number of people.'"),
    ("error_correction", "advanced",
     "I am looking forward to meet you.",
     "Nearly there! 'Looking forward to' is tricky — that 'to' is a preposition, not part of the infinitive. So it needs '-ing': 'I am looking forward to meeting you.'",
     "After 'look forward to', the following verb takes the gerund form because 'to' functions as a preposition, not an infinitive marker."),
    ("error_correction", "intermediate",
     "I am boring in this class.",
     "Careful — that means YOU are boring (not interesting)! You mean 'I am bored in this class.' -ED = how you feel. -ING = what causes the feeling.",
     "Participial adjective error: 'boring' describes the stimulus, 'bored' the experiencer."),
    ("error_correction", "beginner",
     "I am student.",
     "Just add 'a'! 'I am a student.' In English, jobs and roles need 'a' or 'an' before them. 'I am a teacher', 'I am an engineer'. Try another one!",
     "Singular countable nouns require a determiner. Correct: 'I am a student.'"),
]

for dim, lvl, prompt, chosen, rejected in MORE_ERRORS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# --- Additional vocabulary pairs (verbosity, mixed) -------------------------
MORE_VOCAB = [
    ("beginner", "What does 'maybe' mean?",
     "It means possibly — not yes, not no, somewhere in between. 'Maybe I'll go to the party.' It shows you're not sure yet.",
     "'Maybe' is an adverb expressing epistemic uncertainty, functioning as a sentence-level modifier."),
    ("beginner", "What is 'weekend'?",
     "Saturday and Sunday — the days you don't work or go to school! 'What are you doing this weekend?' is a very common question.",
     "'Weekend' refers to the period from Saturday to Sunday in most Western cultures, or Friday to Saturday in others."),
    ("beginner", "What does 'mistake' mean?",
     "Something you did wrong by accident — not on purpose. 'I made a mistake on the test.' Everyone makes mistakes, especially when learning! It's okay.",
     "'Mistake' is a noun denoting an error or incorrect action, often unintentional."),
    ("intermediate", "What does 'take it for granted' mean?",
     "To not appreciate something because you're used to it. 'I took clean water for granted until I traveled abroad.' What do you take for granted?",
     "'Take for granted' is a verbal idiom meaning to fail to appreciate the value of something due to familiarity or habitual use."),
    ("intermediate", "What does 'the last straw' mean?",
     "The final small problem that makes someone finally lose patience — like one straw that breaks the camel's back. 'His lateness was the last straw — I quit!'",
     "'The last straw' is a truncation of the idiom 'the straw that broke the camel's back', denoting the final minor event in a cumulative series."),
    ("advanced", "What does 'gaslighting' mean?",
     "Making someone question their own reality — 'You didn't see that' when they did. It's a form of manipulation. The word comes from a 1944 movie called 'Gaslight.'",
     "'Gaslighting' is a form of psychological manipulation where the perpetrator seeks to make the target doubt their own perception, memory, or sanity."),
    ("advanced", "What does 'cognitive dissonance' mean?",
     "The uncomfortable feeling when your actions don't match your beliefs — like knowing junk food is bad but eating it anyway. Your brain doesn't like the contradiction.",
     "'Cognitive dissonance' is a psychological construct proposed by Leon Festinger describing the mental discomfort arising from holding contradictory beliefs, values, or attitudes."),
    ("intermediate", "What does 'red flag' mean in modern English?",
     "A warning sign — especially about people. 'He never apologizes — that's a red flag.' It means watch out, something's not right. What's a red flag for you?",
     "A 'red flag' is a metaphorical warning indicator, currently widely used in informal discourse to denote problematic behaviors in interpersonal relationships."),
    ("beginner", "What does 'upset' mean?",
     "Unhappy and a little angry or sad — 'She was upset when she lost her keys.' It's between sad and angry. Can you use it in a sentence?",
     "'Upset' is a multifunctional word that can serve as an adjective, verb, or noun, generally denoting emotional disturbance."),
    ("advanced", "What's the difference between 'continual' and 'continuous'?",
     "'Continual' = happening repeatedly with breaks. 'Continuous' = non-stop, no breaks. 'Continual interruptions' vs 'continuous rain.' One has pauses, one doesn't!",
     "'Continual' denotes intermittent recurrence while 'continuous' denotes uninterrupted duration. The distinction is aspectual."),
]

for lvl, prompt, chosen, rejected in MORE_VOCAB:
    pairs.append(("verbosity", lvl, prompt, chosen, rejected))

# --- Final scaffolding expansion (mixed levels) ----------------------------
FINAL_SCAFFOLDING = [
    ("beginner", "How do I describe my daily routine?",
     "Start with waking up and go through your day. 'I wake up at 7. I eat breakfast. I go to work.' What do you do first in the morning?",
     "Describe your daily routine using the present simple tense with time adverbials."),
    ("beginner", "How do I talk about the weather?",
     "Easy ones: 'It's hot', 'It's cold', 'It's raining.' For more detail: 'It's a sunny day.' Look outside right now — what's the weather?",
     "Weather descriptions use the dummy subject 'it' with weather adjectives or continuous forms."),
    ("intermediate", "How do I tell a story in English?",
     "Use past tense and time words: 'First... then... after that... finally...' Start with setting the scene. What's a funny thing that happened to you recently?",
     "Narrative structure in English follows Labov's model: abstract, orientation, complicating action, evaluation, resolution, and coda."),
    ("intermediate", "How do I express opinions without sounding aggressive?",
     "'I think...', 'In my view...', 'From my perspective...' all soften your opinion. Compare: 'You're wrong!' vs 'I see it differently.' Which invites conversation?",
     "Opinion hedging in English employs epistemic markers, perspective markers, and tentativity signals to reduce illocutionary force."),
    ("advanced", "How do I paraphrase effectively?",
     "Change the structure, not just the words. 'The study found that exercise helps sleep' → 'According to the research, physical activity improves sleep quality.' Try one!",
     "Paraphrasing involves restructuring at the syntactic level and substituting at the lexical level while preserving semantic content."),
    ("advanced", "How do I use rhetorical questions in presentations?",
     "They make the audience think without expecting an answer. 'But what if we could change that?' — then pause. The silence does the work. Try one for your topic.",
     "Rhetorical questions are interrogatives not seeking information but designed for persuasive or emphatic effect."),
]

for lvl, prompt, chosen, rejected in FINAL_SCAFFOLDING:
    pairs.append(("scaffolding", lvl, prompt, chosen, rejected))

# ─── BATCH 4: FINAL 42+ PAIRS ───────────────────────────────────────────────

FINAL_BATCH = [
    # turn_taking (targeting ~100)
    ("turn_taking", "beginner",
     "Can you teach me animals?",
     "Sure! What's your favorite animal? Tell me and I'll teach you five more related ones.",
     "Animals in English are classified into various categories including mammals, reptiles, amphibians, birds, fish, and invertebrates. Let me start with a comprehensive overview."),
    ("turn_taking", "beginner",
     "I want to practice greetings.",
     "Great! I'll be a stranger at a party. Walk up to me — what do you say?",
     "Greeting sequences in English consist of an adjacency pair structure. The first pair part is typically an attention-getter or formulaic opener, followed by a reciprocal response."),
    ("turn_taking", "beginner",
     "This is fun!",
     "I'm glad! What part are you enjoying most? Let's do more of that.",
     "Positive affect in language learning is associated with increased motivation, willingness to communicate, and overall engagement. Research by Dörnyei and others has established that enjoyment is a key predictor of sustained language learning effort."),
    ("turn_taking", "intermediate",
     "I tried to use this word today but nobody understood me.",
     "How did you pronounce it? Say it for me now and I'll listen carefully.",
     "Communication breakdowns can result from various factors including phonological errors, inappropriate word choice, pragmatic transfer, or register mismatch."),
    ("turn_taking", "intermediate",
     "My English teacher at school used to only teach grammar, not speaking.",
     "That's changing now! Speaking practice is what makes it real. Let's make up for it — what topic should we talk about?",
     "Traditional grammar-translation methodology has been criticized for its failure to develop communicative competence. The communicative approach, developed in response, emphasizes meaningful interaction."),
    ("turn_taking", "advanced",
     "I read a lot in English but I never get to practice speaking.",
     "Let's fix that right now. Pick any topic from something you read recently — tell me about it in 60 seconds. Go!",
     "The input-output asymmetry in L2 development is well-documented. While extensive reading provides rich input, productive speaking skills require pushed output opportunities."),
    ("turn_taking", "advanced",
     "How do I handle being corrected by a native speaker?",
     "Take it as a gift! Say 'Thanks, I'll remember that.' Most people correct you because they want to help. What's a correction you've received recently?",
     "Error correction in naturalistic interaction follows specific sequential patterns including other-initiated repair, embedded correction, and exposed correction."),
    ("turn_taking", "intermediate",
     "Sorry, I didn't catch what you said about articles.",
     "No problem! Short version: 'a/an' = any one thing. 'The' = a specific thing. Want me to give you a quick exercise?",
     "Let me repeat the comprehensive explanation of the English article system, covering definite, indefinite, and zero articles across all their usage contexts."),
    ("turn_taking", "beginner",
     "I practice alone at home. Is that okay?",
     "Absolutely! Talk to yourself, narrate your actions — 'Now I am cooking rice.' It sounds funny but it works! What do you usually do at home?",
     "Self-directed practice is a form of autonomous learning that can contribute to interlanguage development. Private speech and self-talk have been shown to serve important cognitive and regulatory functions."),
    ("turn_taking", "advanced",
     "I want to improve my vocabulary but flashcards are boring.",
     "Then ditch them! Read things you actually enjoy — articles, Reddit, novels. When you see a new word, use it in a sentence RIGHT THEN. What do you like reading?",
     "Incidental vocabulary acquisition through extensive reading has been shown to be more effective than deliberate study for long-term retention."),

    # difficulty_calibration (targeting ~100)
    ("difficulty_calibration", "beginner",
     "What is a sentence?",
     "A sentence is a complete thought with a subject (who/what) and a verb (does what). 'The cat sleeps.' — that's a sentence! Can you make one?",
     "A sentence is a syntactic unit consisting minimally of a subject NP and a predicate VP, which together form a complete proposition."),
    ("difficulty_calibration", "beginner",
     "How do I spell my name in English?",
     "Use the English alphabet! A-B-C-D... Just say each letter of your name. What's your name? I'll help you spell it out.",
     "English orthographic representation of proper nouns follows grapheme-phoneme correspondence rules, though transliteration from non-Latin scripts may require IPA-based approximation."),
    ("difficulty_calibration", "intermediate",
     "How do I talk about my future plans?",
     "'I'm going to...' for plans you've already decided. 'I might...' for maybes. What are your plans for next week?",
     "Future reference in English is expressed through multiple competing forms including 'will', 'going to', present continuous, present simple, and 'be about to', each with distinct semantic and pragmatic constraints."),
    ("difficulty_calibration", "intermediate",
     "I need to prepare for a job interview in English.",
     "Key phrases: 'I have experience in...', 'My strength is...', 'I'm passionate about...' What position is it? Let's practice the most likely questions.",
     "Job interview discourse requires mastery of self-presentation strategies, institutional speech genres, and impression management techniques."),
    ("difficulty_calibration", "advanced",
     "I want to sound more diplomatic in English.",
     "Use conditionals and hedges: 'Would it be possible...' instead of 'Can you...', 'I wonder if...' instead of 'I want...'. Try softening: 'Give me the report.'",
     "Diplomatic language in English relies on indirectness, hedging devices, conditional constructions, and off-record politeness strategies as theorized by Brown and Levinson."),
    ("difficulty_calibration", "advanced",
     "How do I express disagreement in academic writing?",
     "'While Smith (2020) argues X, this overlooks Y.' Or: 'This analysis, however, does not account for...' It's firm but respectful. What argument are you countering?",
     "Academic disagreement is expressed through a repertoire of rhetorical moves including concession-counterargument structures, hedged critiques, and evidential challenges."),
    ("difficulty_calibration", "beginner",
     "I want to talk about food I like.",
     "Easy! 'I like...' and 'I don't like...' What's your favorite food? Tell me and I'll teach you how to describe it!",
     "Food preference expressions in English utilize stative verbs of affect (like, love, enjoy, prefer) with count and mass noun complements."),
    ("difficulty_calibration", "intermediate",
     "How do I describe a picture in English?",
     "Start with the big picture: 'There is/are...' Then details: 'On the left...', 'In the background...' Describe something you can see right now!",
     "Picture description tasks require spatial language including locative prepositions, existential constructions, and progressive aspect for ongoing actions."),

    # verbosity (targeting ~100)
    ("verbosity", "beginner",
     "What does 'remember' mean?",
     "To keep something in your mind — the opposite of 'forget'. 'I remember your name!' Can you remember a new English word from today?",
     "'Remember' is a cognitive verb in English meaning to retain information in long-term memory. It functions both transitively and intransitively and can take various complement types."),
    ("verbosity", "beginner",
     "What does 'dangerous' mean?",
     "Something that can hurt you — not safe. 'Don't touch that, it's dangerous!' Like fire or a wild animal. What's dangerous near your home?",
     "'Dangerous' is an adjective derived from the noun 'danger' with the suffix '-ous'. It denotes a state of potential harm or risk."),
    ("verbosity", "intermediate",
     "What does 'sarcastic' mean?",
     "Saying the opposite of what you mean, usually in a funny or mean way. 'Oh great, another Monday!' — when you clearly don't like Mondays.",
     "'Sarcastic' is an adjective describing speech characterized by verbal irony with intent to mock, wound, or show contempt."),
    ("verbosity", "intermediate",
     "What does 'procrastinate' mean?",
     "To delay doing something you should be doing — like scrolling your phone instead of studying! 'Stop procrastinating and start your homework.'",
     "'Procrastinate' is a verb derived from the Latin 'procrastinare' meaning to defer action. It involves the voluntary, irrational delay of an intended course of action."),
    ("verbosity", "advanced",
     "What does 'serendipity' mean?",
     "Finding something wonderful by accident — like discovering your favorite café because you got lost. It's a beautiful word! Has serendipity ever happened to you?",
     "'Serendipity' is a noun coined by Horace Walpole in 1754, derived from the Persian fairy tale 'The Three Princes of Serendip'. It denotes the occurrence of fortunate discoveries by accident."),
    ("verbosity", "advanced",
     "What's the difference between 'envy' and 'jealousy'?",
     "Envy = wanting what someone else has. Jealousy = fearing someone will take what you have. 'I envy his car' vs 'I'm jealous of his attention to my partner.' Different emotions!",
     "'Envy' and 'jealousy' are often used interchangeably in casual usage but differ semantically. Envy involves two parties and is about desiring what another possesses. Jealousy involves three parties and concerns the fear of losing something to a rival."),

    # scaffolding (bonus)
    ("scaffolding", "beginner",
     "How do I say what I want?",
     "'I want...' plus the thing! 'I want water.' 'I want to sleep.' For polite: 'I would like...' Which sounds friendlier to you?",
     "Use 'I want' plus a noun or 'to + infinitive'. For politeness, use 'I would like'."),
    ("scaffolding", "intermediate",
     "How do I compare two things?",
     "Add '-er' to short words: 'bigger', 'faster'. Use 'more' with long words: 'more beautiful'. Can you compare two cities you know?",
     "Comparative forms use '-er' for monosyllabic adjectives and 'more' for polysyllabic ones, with some irregular forms."),
    ("scaffolding", "advanced",
     "How do I write a strong opening sentence for an essay?",
     "Start with something surprising, a question, or a bold claim. NOT 'In this essay I will...' — that's boring! What's your essay about? Let's brainstorm an opener.",
     "Effective essay introductions employ hooks such as provocative questions, surprising statistics, or anecdotes."),
    ("scaffolding", "intermediate",
     "How do I use 'wish' properly?",
     "For right now: 'I wish I HAD more time' (past tense, even though it's about now — weird, right?). For the past: 'I wish I HAD STUDIED harder.' What do you wish for?",
     "'Wish' takes past tense for present situations and past perfect for past regrets due to counterfactual semantics."),
]

for dim, lvl, prompt, chosen, rejected in FINAL_BATCH:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# ─── BATCH 5: LAST 15 PAIRS ─────────────────────────────────────────────────
LAST_PAIRS = [
    ("turn_taking", "beginner",
     "I keep forgetting new words.",
     "That's normal! Try using each new word three times today. What word did you learn most recently?",
     "Memory consolidation for L2 vocabulary involves encoding, storage, and retrieval processes. Spacing effects and retrieval practice are the most evidence-based strategies."),
    ("turn_taking", "intermediate",
     "I want to practice but I don't have anyone to talk to.",
     "You've got me! Plus, try talking to yourself — describe what you're doing. 'Now I'm making tea.' It really works!",
     "Opportunities for output practice can be created through self-talk, shadowing, journal writing, and participation in online language exchange platforms."),
    ("turn_taking", "advanced",
     "Can we practice debating a topic?",
     "Yes! Here's a statement: 'Social media does more harm than good.' You have 60 seconds to argue FOR it. Go!",
     "Debate practice in English develops argumentation skills including claim-evidence-reasoning structures, rebuttal techniques, and persuasive language."),
    ("difficulty_calibration", "beginner",
     "What is the alphabet?",
     "It's the 26 letters from A to Z! Let's say them together: A, B, C... Can you continue?",
     "The English alphabet is a Latin-derived script consisting of 26 graphemes, each with upper and lower case allographs."),
    ("difficulty_calibration", "intermediate",
     "How do I describe emotions beyond just 'happy' and 'sad'?",
     "Great question! Instead of 'happy': thrilled, grateful, content. Instead of 'sad': disappointed, heartbroken, melancholy. Which emotion do you feel right now?",
     "The English emotion lexicon extends well beyond basic affects, encompassing nuanced states distinguishable along dimensions of valence, arousal, and dominance."),
    ("difficulty_calibration", "advanced",
     "How do I make my English sound more natural and less textbook-y?",
     "Three quick wins: use contractions ('I'm' not 'I am'), add discourse markers ('well', 'you know', 'I mean'), and use phrasal verbs ('find out' not 'discover'). Try converting: 'I do not understand what you are saying.'",
     "Naturalness in spoken English correlates with the use of contracted forms, informal lexis, discourse markers, ellipsis, and reduced forms."),
    ("verbosity", "beginner",
     "What does 'practice' mean?",
     "Doing something again and again to get better at it. 'Practice makes perfect!' What do you practice?",
     "'Practice' is both a noun and verb (American English) denoting the repeated exercise of an activity to develop or maintain proficiency."),
    ("verbosity", "intermediate",
     "What does 'overthink' mean?",
     "Thinking about something too much until it becomes a problem. 'Stop overthinking — just try!' Do you overthink in English?",
     "'Overthink' is a compound verb with the prefix 'over-' indicating excess. It means to think about something excessively."),
    ("verbosity", "advanced",
     "What does 'devil's in the details' mean?",
     "Small details can cause big problems — something looks easy until you look closely. 'The contract seemed fine, but the devil's in the details.'",
     "'The devil is in the details' is a proverbial expression warning that overlooked specifics can be problematic."),
    ("scaffolding", "beginner",
     "How do I ask for help in English?",
     "'Can you help me?' is the simplest. 'Excuse me, could you help me please?' is politer. Try the polite version!",
     "Use 'Can you help me?' or the more polite 'Could you help me, please?'"),
    ("scaffolding", "intermediate",
     "How do I give directions to someone?",
     "Use these key phrases: 'Go straight', 'Turn left/right', 'It's on your left.' Imagine someone outside your house — how would you direct them to the nearest shop?",
     "Direction-giving requires spatial language including movement verbs, locative prepositions, and landmark references."),
    ("scaffolding", "advanced",
     "How do I summarize a long text effectively?",
     "Find the main argument first — what's the ONE thing the author is saying? Then pick 2-3 supporting points. Leave out examples and details. Try it on the last article you read.",
     "Summarization involves identifying the macrostructure through deletion, generalization, and construction rules."),
    ("error_correction", "beginner",
     "I have 20 years old.",
     "In English we use 'am' for age, not 'have'! 'I am 20 years old.' In your language you probably say 'have' — that's a common mix-up. Try it the English way!",
     "'Have' is incorrect for expressing age in English. Use 'be': 'I am 20 years old.'"),
    ("error_correction", "intermediate",
     "She said me that she was coming.",
     "Almost! 'Say' doesn't take an indirect object — use 'told' instead: 'She told me that she was coming.' Or: 'She said that she was coming.' Which sounds more natural to you?",
     "'Say' does not take an indirect object. Use 'tell' with an indirect object or 'say' without one."),
    ("error_correction", "advanced",
     "I've been to Paris last summer.",
     "Tricky one! 'Last summer' is a finished time, so we need simple past: 'I went to Paris last summer.' Use 'I've been to Paris' when the time doesn't matter — it just means you have the experience.",
     "Present perfect cannot be used with definite past time adverbials. Use simple past: 'I went to Paris last summer.'"),
    ("turn_taking", "beginner",
     "Thank you for helping me!",
     "You're very welcome! You did great today. See you next time!",
     "You're welcome! Gratitude is an important social function in English. There are many ways to respond to thanks, including 'You're welcome', 'No problem', 'My pleasure', 'Don't mention it', 'Not at all', and 'Anytime'. The choice depends on the level of formality."),
]

for dim, lvl, prompt, chosen, rejected in LAST_PAIRS:
    pairs.append((dim, lvl, prompt, chosen, rejected))

# ─── DEDUPLICATE & TRIM TO 500 ─────────────────────────────────────────────────
seen_prompts = set()
unique_pairs = []
for p in pairs:
    key = p[2][:80].lower().strip()
    if key not in seen_prompts:
        seen_prompts.add(key)
        unique_pairs.append(p)

print(f"Total unique pairs generated: {len(unique_pairs)}")
if len(unique_pairs) < 500:
    print(f"WARNING: Only {len(unique_pairs)} unique pairs — need more templates!")

# Shuffle to mix dimensions/levels, then trim to 500
random.shuffle(unique_pairs)
final_pairs = unique_pairs[:500]

# ─── WRITE JSONL ───────────────────────────────────────────────────────────────
output_path = "data/fluento_dpo_500.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for i, (dim, lvl, prompt, chosen, rejected) in enumerate(final_pairs):
        record = {
            "id": i + 1,
            "dimension": dim,
            "learner_level": lvl,
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ─── STATS ─────────────────────────────────────────────────────────────────────
from collections import Counter
dim_counts = Counter(p[0] for p in final_pairs)
lvl_counts = Counter(p[1] for p in final_pairs)
print("\nDimension distribution:")
for k, v in sorted(dim_counts.items()):
    print(f"  {k}: {v}")
print("\nLevel distribution:")
for k, v in sorted(lvl_counts.items()):
    print(f"  {k}: {v}")
print(f"\nFile written to: {output_path}")
print(f"Total records: {len(final_pairs)}")
