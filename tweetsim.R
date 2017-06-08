library(readr)
library(dplyr)

tweets <- read_csv("/Users/alexanderfurnas/Projects/SemanticSmithWaterman/data/congress_tweets.csv")
tweet_sim <- read_csv("/Users/alexanderfurnas/Projects/SemanticSmithWaterman/tweet_comparisons.csv")

tweet_sim <- filter(tweet_sim, query_docid <= 100000)

tweet_sim <- mutate(tweet_sim, score_diff = ssw_score - sw_score)

tweet_sim <- filter(tweet_sim, query_docid != result_docid)

library(ggplot2)

ggplot(tweet_sim, aes()) +geom_density(aes(x=sw_score), color="blue")  +geom_density(aes(x=ssw_score), color="red") +theme_minimal(base_size = 24) +scale_x_log10() +xlab("Score")

ggplot(filter(tweet_sim, sw_score >90), aes()) +geom_density(aes(x=sw_score), color="blue")  +geom_density(aes(x=ssw_score), color="red") +theme_minimal(base_size = 24)  +xlab("Score")


ggplot(filter(tweet_sim, score_diff >0), aes()) +geom_density(aes(x=score_diff), color="dark green") +theme_minimal(base_size = 24) +xlab("Difference between SW and SSW") +xlab("Score")

tweet_sim <- arrange(tweet_sim, desc(score_diff, sw_score))

tweet_simsum <- filter(tweet_sim, score_diff > 20)



m_tweets <- select(tweets, X1, text)

tweet_simsum <- left_join(tweet_simsum, m_tweets, by=c("query_docid" = "X1"))
tweet_simsum <- left_join(tweet_simsum, m_tweets, by=c("result_docid" = "X1"))

tweet_simsum_top <- filter(tweet_simsum, ssw_score >105)


filter(tweets, index == 23308)

tweet_simsum_top <- filter(tweet_simsum_top, !(query_docid %in% result_docid))

write_csv(tweet_simsum_top, "/Users/alexanderfurnas/Projects/SemanticSmithWaterman/data/top_diff.csv")



pairs <- filter(tweet_sim, ssw_score >105)
pairs <- filter(pairs, !(query_docid %in% result_docid))

tweet_dat <- dplyr::select(tweets, X1,state, rep, dem, incumb, screenname)
tweet_dat

pairs <- left_join(pairs, tweet_dat, by = c( "query_docid" = "X1"))
pairs <- left_join(pairs, tweet_dat, by = c( "result_docid" = "X1"))
pairs$same_party <- 0
pairs$same_party[pairs$rep.x == 1 & pairs$rep.y == 1 | pairs$dem.x == 1 & pairs$dem.y == 1 ] <- 1

pairs$same_state <- 0
pairs$same_state[pairs$state.x ==  pairs$state.y] <- 1

summary(c(pairs$incumb.y,pairs$incumb.x))

library(statnet)

max(tweet_sim$query_docid)
max(tweet_sim$result_docid)

tweet_edgelist <- summarise(group_by(pairs, screenname.x, screenname.y), numtweets = n())

tweet_edgelist <- left_join(tweet_edgelist, unique(dplyr::select(pairs, screenname.x, screenname.y, dem.x, rep.x, dem.y, rep.y, same_party, same_state)))

tweet_edgelist <- filter(tweet_edgelist, !(screenname.x == screenname.y))
g=graph.data.frame(dplyr::select(tweet_edgelist, screenname.x, screenname.y, numtweets),directed=FALSE)

plot(g, vertex.label=NA, vertex.size=3)

user_party <- unique(select(tweet_edgelist, screenname.x, rep.x, dem.x))
user_party2 <- unique(select(ungroup(tweet_edgelist), screenname.y, rep.y, dem.y))
names(user_party2) <- c("screenname.x", "rep.x", "dem.x")
user_party <- as.data.frame(rbind(ungroup(user_party), user_party2))

user_party$party <- "other"
user_party$party[user_party$rep.x == 1] <- "rep"
user_party$party[user_party$dem.x == 1] <- "dem"
user_party <- filter(user_party, screenname.x %in% V(g)$name)
user_party <- unique(user_party)


num_parties <- summarise(group_by(user_party,screenname.x), n = n())
num_parties <- arrange(num_parties, desc(n))

user_party <- filter(user_party, !(screenname.x == "RepBillJohnson" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepBuddyCarter" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepDannyDavis" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepDaveBrat" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepDennisRoss" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepDennyHeck" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepJudyChu" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepMikeCoffman" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepPaulCook" & dem.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepPaulCook" & dem.x == 0 & rep.x==0))
user_party <- filter(user_party, !(screenname.x == "RepRonKind" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepScottPeters" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "RepThompson" & rep.x == 1))
user_party <- filter(user_party, !(screenname.x == "USRepGaryPalmer" & dem.x == 1))



V(g)$party <- user_party$party
V(g)$color[V(g)$party == "dem"] <- "blue"
V(g)$color[V(g)$party == "rep"] <- "red"
E(g)$weight <- tweet_edgelist$numtweets
g_simp <- simplify(g, remove.multiple = FALSE, remove.loops = TRUE)
plot(g_simp, vertex.label=NA, vertex.size=3, vertex.color=V(g)$color, edge.width = sqrt(E(g)$weight))

tweet_edgelist

