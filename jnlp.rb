# coding: utf-8
require 've'
sentence = ARGV[0]
words = Ve.in('ja').words(sentence)
text = words.collect(&:word)
puts "TOKENS"
puts text
lemmas = words.collect(&:lemma)
puts "LEMMAS"
puts lemmas
parts_of_speech = words.collect(&:part_of_speech)
puts "PARTS OF SPEECH"
puts parts_of_speech
