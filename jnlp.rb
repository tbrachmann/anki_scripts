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
