##########################################################################
# JHurwitz
# Individual Assignment
# G28953928

# Mapping Birthrate
#Source: https://www.mirosa.org/blog/post/2015/01/Maps-in-R/#

##########################################################################

#-------------------------------------------------------------------------
# Download map template, load libraries, and set map theme options
#-------------------------------------------------------------------------

setwd("C:/Users/jhurwitz/Desktop/GW/2015_Fall/Programming for Analytics/Modules")
download.file("http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip", destfile="ne_110m_admin_0_countries.zip")
unzip("ne_110m_admin_0_countries.zip")

library(rgdal)
library(ggplot2)
library(plyr)
library(dplyr)
library(scales)
library(RJSONIO)
library(WDI)
library(RColorBrewer)
library(maptools)


theme_opts <- list(theme(panel.grid.minor = element_blank(),
                         panel.grid.major = element_blank(),
                         panel.background = element_blank(),
                         plot.background = element_rect(fill="white"),
                         panel.border = element_blank(),
                         axis.line = element_blank(),
                         axis.text.x = element_blank(),
                         axis.text.y = element_blank(),
                         axis.ticks = element_blank(),
                         axis.title.x = element_blank(),
                         axis.title.y = element_blank(),
                         plot.title = element_text(size=22)))

wmap_countries <- readOGR(dsn=".", layer="ne_110m_admin_0_countries")
wmap_countries_robin <- spTransform(wmap_countries, CRS("+proj=robin"))
wmap_countries_robin_df <- fortify(wmap_countries_robin)

wmap_countries_robin@data$id <- rownames(wmap_countries_robin@data)
wmap_countries_robin_df_final <- join(wmap_countries_robin_df, wmap_countries_robin@data, by="id")

new_cache <- WDIcache()

#-------------------------------------------------------------------------
# Prepare data and generate map
#-------------------------------------------------------------------------

# Download birth rate data
birth = WDI(indicator='SP.DYN.CBRT.IN', country="all", start=1981, end=2013)

# Remove NAs
birth <- subset(birth, !is.na(birth$SP.DYN.CBRT.IN))

# Return most recent year data for each country
birth <- group_by(birth, country)
birth <- filter(birth, year == max(year))

# Mapping prep name match
names(birth)[1] <- "iso_a2"

# Join poverty data to existing map
final <- left_join(wmap_countries_robin_df_final, birth, by="iso_a2")

# Set buckets
final$birthrange <- cut(final$SP.DYN.CBRT.IN, breaks=c(0,10,20,30,40,50), ordered_result=TRUE)

# Plot
ggplot(subset(final, !continent == "Antarctica")) + 
  geom_polygon(aes(long, lat, group = group, fill = birthrange)) + 
  geom_path(aes(long, lat, group = group), color="white") + 
  scale_fill_brewer("Birth Rate, crude (per 1,000 people)", type = "seq", palette = "Blues", na.value = "grey50") + 
  theme_opts + coord_equal(xlim=c(-13000000,16000000), ylim=c(-6000000,8343004))

