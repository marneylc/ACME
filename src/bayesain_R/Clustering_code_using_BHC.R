####################################################################################
### 
# Clustering Code using BHC (using BHC R/BHC and Rgplots)
# code for reproducible research (prepared for CODECHECK codecheck.org.uk)
#
# This code is part of, and published under the same terms and conditions as, the following publication 
# Nienyun Sharon Hsu, Erika Wong En Hui, Mengzhen Liu, Di Wu, Thomas A. Hughes & James Smith,
# (2021). Revealing nuclear receptor hub modules from Basal-like breast cancer expression networks.
# PLOS ONE
#
# Code authored N Hsu and J Smith (2016-2020)
# was first written for R(v3.5.3), R Studio(v1.2.5019),
# R/Bioconductor (3.10), R/BHC (v1.38.0)
# Last tested on  R(v4.0.4), R Studio(v1.4.1103),
# R/Bioconductor (3.10), R/BHC (v1.42.0)
# 
# Recommended first use is to manually execute each Stage incrementally in RStudio.
# Recommended folder organisation:
# ~/Analysis/
# ~/Analysis/Data/  for .csv data input files 
# ~/Analysis/Working_directory/  for Rdata files and output .txt and .pdf files
#
# This cluster analysis uses,
# Non-parametric Multinomial Bayesian Hierarchical clustering R/Bioconductor/BHC  
# for Latent feature detection in patient-gene expression data DOI: 10.18129/B9.bioc.BHC
# R/BHC Requires a prior Bioconductor installation, see https://www.bioconductor.org/install/
#
# Text output files list the cluster membership.
#
# The Visualisation requires,
# R/gplots  https://cran.r-project.org/web/packages/gplots/index.html
# and gplots::heatmap.2 Enhanced Heat Map to represent the multinomial data
# Black = marginal likelihood, the signal contributions
# Red = upperbound, silent contributions
# Green = lowerbound, silent contributions
#
###
####################################################################################
### STAGE 1 - Initiation
####################################################################################

cat("\014") ## clear RStudio console
rm(list=ls()) ## clear the Global Environment

### working directory 
### Example TCGA Analysis folder
setwd("~/Basal_vs_LuminalB/Working_directory/") 

### The example here is for clustering TCGA data which was already median-centred.
### For the BRCA_METABRIC data, the alternative code was employed

### TCGA
### Example .csv file, see  SI_3_4  Original data was median-centred (autoscaled)
signal_data <- read.csv("../Data/TCGA_BA+LUB_171genes.csv", row.names = 1) 

### METABRIC
### load .csv file
# metabric_data <- read.csv("../Data/METABRIC_BA+LUB_169genes.csv", row.names = 1, col.names =,1)
# metabric_data <- metabric_data[-1,] # optional
### median-centre
# rowmed <- apply(metabric_data,1,median)
# mediancentred_data <- metabric_data - rowmed
# signal_data <- mediancentred_data

textRowLabel <-"Genes"
textColLabel <-"Patients"
save(textRowLabel, file="textRowLabel.Rda")
save(textColLabel, file="textColLabel.Rda")

### Specific row and col editing for TCGA data
n_col<-ncol(signal_data) 
n_row<-nrow(signal_data)
new_row_names <- rep("X",n_row)
for (i in seq(n_row)){ new_row_names[i]<-paste0(row.names(signal_data)[i])}
row.names(signal_data) <- new_row_names

### Example for TCGA data here 
for (i in seq(n_col)){ colnames(signal_data)[i] <-gsub("TCGA.", "",colnames(signal_data)[i]) }
 
X_original <- as.data.frame(signal_data)

####################################################################################
### STAGE 2 - Repeat this for re-calibration of thresholds, if necessary. 
####################################################################################
### information content assessment ie row and col elimination if too many 0s (== N/As!)
### examination of data with large fraction of missing values requires calibration
###  
### Subset_data  only keeps rows and columns with complete information below threshold
### (only minimal amounts of missing data)

### Replace NAs with 0
X <- X_original
X[is.na(X)] <- 0

### row filter - acceptable threshold of missing data in rows
### row threshold established empirically for TCGA and METABRIC data
###  eg 1/8 is the most generous, 1/16, 1/32, 1/64 etc
threshold_r <- 1/64 

row_data_flag <- rep(1, nrow(X)) 
for (i in seq(nrow(X))){ if(length(which(X[i,]==0)) > threshold_r*(ncol(X))) { row_data_flag[i]<-0} }
acceptable_rows <- which(row_data_flag==1) ### important
rejected_rows <- which(row_data_flag==0) ### important information
length(rejected_rows) ### for information
rejectedRData_file <- paste0("rejectedrows", ".Rda") 
save(rejected_rows, file=rejectedRData_file) ### saved for information

### column filter - acceptable threshold of missing data in rows
### col threshold established empirically for TCGA and METABRIC data
###  eg 1/8 is the most generous, 1/16, 1/32, 1/64 etc
threshold_c <-1/32 

col_data_flag <- rep(1, ncol(X))
for (i in seq(ncol(X))){ if (length(which(X[,i]==0)) > threshold_c*(nrow(X))) { col_data_flag[i]<-0} }
acceptable_cols <- which(col_data_flag==1) ### important
rejected_cols <- colnames(X)[which(col_data_flag==0)] 
length(rejected_cols) ### for information
rejectedCData_file <- paste0("rejectedcols", ".Rda")
save(rejected_cols, file=rejectedCData_file)  ### saved for information

subset_data <- X[acceptable_rows,acceptable_cols] ### subsetting for Complete data

####################################################################################
### STAGE 3 (optional)
####################################################################################
### To show ordination does not bias the process, we randomise rows and columns.
### We believe BHC is not affected by order.

### Warning heatmap.2 function visualisation compositing might break down with v large data,
### so user could test with a fraction of the data first:
data_fraction <-1.0 ### 1.0 = maximum

new_r_length <- as.integer(data_fraction*length(acceptable_rows))
new_c_length <- as.integer(data_fraction*length(acceptable_cols))

### Randomise rows and columns
rnd_pointers_r <- sample(acceptable_rows, new_r_length,replace=FALSE)
rnd_pointers_c <- sample(acceptable_cols, new_c_length,replace=FALSE) 

### subsetting for Complete data
subset_data <- as.data.frame(matrix(0, nrow=new_r_length , ncol=new_c_length))
for(i in seq(1:length(rnd_pointers_r))) { 
   for(j in seq(1:length(rnd_pointers_c))) { 
      subset_data[i,j] <- X[rnd_pointers_r[i], rnd_pointers_c[j]]
      } 
   }  
row.names(subset_data) <- rownames(X)[rnd_pointers_r]
colnames(subset_data) <- colnames(X)[rnd_pointers_c] 
rm(i,j)

### doing this to save memory 
rm(signal_data,X) ### optional

Xbhc <- subset_data
rm(subset_data) ### optional
save (Xbhc, file="Xbhc.Rda") ### backup 

####################################################################################
### STAGE 4 - Run R/BHC
####################################################################################

library(BHC) 

### Based on R/BHC Examples - FOR THE MULTINOMIAL CASE, THE DATA CAN BE DISCRETISED
col_names_for_BHC <- colnames(Xbhc)
row_names_for_BHC <- row.names(Xbhc)

### Assume n > p
nDataItems <- nrow(Xbhc) ### (n)
nFeatures <- ncol(Xbhc)  ### (p)

### numThreads is 1 (default) or more, depending on the available cores for speed
nt <- 2
### robustFlag is 0 (default) to use single Gaussian likelihood, 1 to use mixture likelihood.
robust <- 1

percentiles_a <- FindOptimalBinning(Xbhc, row_names_for_BHC, transposeData=TRUE, verbose=TRUE)
discreteData_temp <- DiscretiseData(t(Xbhc), percentiles=percentiles_a) # apply to transform by default
discreteData_a <- t(discreteData_temp)
save(discreteData_a,file="discretizedData_a.Rda")
save(percentiles_a,file="percentiles_a.Rda")
rm(discreteData_temp)
hc_a <- bhc(discreteData_a, row_names_for_BHC, verbose=TRUE, robust=robustFlag, numThreads=nt)
save(hc_a, file="hc_a.Rda")
txt_file_a <- paste0("hc_labels_",textRowLabel,"_a.txt") 
WriteOutClusterLabels(hc_a, txt_file_a, verbose=TRUE)

### requires transform of the data as t(Xbhc), be mindful of the interpretation
percentiles_b <- FindOptimalBinning(t(Xbhc), col_names_for_BHC, transposeData=TRUE, verbose=TRUE)
discreteData_temp <- DiscretiseData(Xbhc, percentiles=percentiles_b) # apply to transform by default
discreteData_b <- t(discreteData_temp)
save(discreteData_b,file="discretizedData_b.Rda")
save(percentiles_b,file="percentiles_b.Rda")
rm(discreteData_temp)
hc_b <- bhc(discreteData_b, col_names_for_BHC, verbose=TRUE, robust=robustFlag, numThreads=nt)
save(hc_b, file="hc_b.Rda")
txt_file_b <- paste0("hc_labels_",textColLabel,"_b.txt") 
WriteOutClusterLabels(hc_b, txt_file_b, verbose=TRUE)

### Stop/restart here if you prefer
####################################################################################
### STAGE 5 - Visualisation recommended with RStudio
####################################################################################

library(gplots)

cat("\014") ### clear RStudio console
rm(list=ls()) ### clear the Global Environment

# Example TCGA Analysis folder
setwd("~/Basal_vs_LuminalB/Working_directory/") 
### Load data
load("Xbhc.Rda")
load("hc_a.Rda")
load("hc_b.Rda")
load("discretizedData_a.Rda")
load("discretizedData_b.Rda")
load("textColLabel.Rda")
load("textRowLabel.Rda")

### Heatmap with heatmap.2() for .pdf file export using Rstudio
### Remember  lower bound = green, Marginal Likelihood = black!, upper bound = red
### Important Note: With newer versions of BHC and gplots libraries,
### the row and column labels are NOT aligned with the plot row widths and column
### widths in the heatmaps. It is important therefore to refer to
### hc_labels_a.txt (see above) and hc_labels_b.txt (see above).
 
ML_a <- as.integer((length(which(discreteData_a[,1]==1))/nrow(discreteData_a))*100)
col_percentiles <- c( ((100-ML_a)/2)*0.01,ML_a*0.01,((100-ML_a)/2)*0.01) 

text_col_percent <- paste(as.character(col_percentiles), collapse=", ")
table_text <- paste0(nrow(Xbhc)," ",textRowLabel," by ",ncol(Xbhc)," ", textColLabel," (",text_col_percent,")")
heatmap.2(t(discreteData_a),trace="none", col=greenred(256),  dendrogram="both", key=FALSE, Rowv=hc_b, Colv=hc_a)
dev.copy(pdf,paste0("Rplot_",table_text,"_a.pdf"))
dev.off()

ML_b <- as.integer((length(which(discreteData_b[1,]==1))/ncol(discreteData_b))*100)
row_percentiles <- c( ((100-ML_b)/2)*0.01,ML_b*0.01,((100-ML_b)/2)*0.01)

text_row_percent <- paste(as.character(row_percentiles), collapse=", ")
table_text <- paste0(ncol(Xbhc)," ",textColLabel," by ",nrow(Xbhc)," ", textRowLabel, " (",text_row_percent,")")
heatmap.2(t(discreteData_b),trace="none", col=greenred(256),  dendrogram="both", key=FALSE, Rowv=hc_a, Colv=hc_b)
dev.copy(pdf,paste0("Rplot_",table_text,"_b.pdf"))
dev.off()
####################################################################################
# end
####################################################################################
