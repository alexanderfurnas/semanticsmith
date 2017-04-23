library(readr)
library(dplyr)
tweets <- read_csv("/Users/alexanderfurnas/Downloads/merged_file_s2_stata.csv")
tweets <- filter(tweets, isretweet == F)

write.csv(tweets, "/Users/alexanderfurnas/Projects/SemanticSmithWaterman/congress_tweets.csv")
