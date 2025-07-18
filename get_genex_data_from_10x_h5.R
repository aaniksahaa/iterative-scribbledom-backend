source("code_utils/read_data/utils.R")
source("code_utils/read_data/installation.R")

# install_libraries()

library(SingleCellExperiment)
library(rhdf5)
library(tidyverse)
library(Matrix)
library(mclust)
library(rjson)

args = commandArgs(trailingOnly=TRUE)
config_file_path <- args[1]

params <- fromJSON(file = config_file_path)

space_ranger_out = params$space_ranger_output_directory
preprocessed_dataset_folder = params$preprocessed_data_folder
dataset = params$dataset
samples = params$samples
n_hvg <- 2000
n_PCs <- params$n_pcs
n_cluster <- params$n_cluster_for_auto_scribble
tech <- params$technology

if (tech == "st") {
  print("Invalid data, give an ST data")
  return(-1)
}

for (sample in samples) {
  dir_name <- sprintf("%s/%s/%s",space_ranger_out,dataset,sample)
  h5_name <- sprintf("%s_filtered_feature_bc_matrix.h5",sample)
  
  # print(dir_name)
  sce <- read10Xh5(dir_name,h5_name)
  sce <- scater::logNormCounts(sce)
  
  set.seed(101)
  dec <- scran::modelGeneVar(sce)
  top <- scran::getTopHVGs(dec, n = n_hvg)
  rowData(sce)[["is.HVG"]] <- (rownames(sce) %in% top)
  
  set.seed(102)
  sce <- scater::runPCA(sce, subset_row=top,ncomponents=n_PCs)
  
  pcs <- sce@int_colData$reducedDims$PCA
  coordinates <- colData(sce)[,c("pxl_row_in_fullres", "pxl_col_in_fullres")]
  
  set.seed(2020)
  mclust_run <- Mclust(pcs,n_cluster,"EEE")
  mclust_result <- mclust_run$classification
  
  preprocessed_data_sample_folder <- sprintf("%s/%s/%s",preprocessed_dataset_folder,dataset,sample)
  pcs_csv_folder <- sprintf("%s/Principal_Components/CSV",preprocessed_data_sample_folder)
  coord_csv_folder <- sprintf("%s/Coordinates",preprocessed_data_sample_folder)
  reading_h5_folder <- sprintf("%s/reading_h5",preprocessed_data_sample_folder)
  
  dir.create(file.path(preprocessed_data_sample_folder), showWarnings = FALSE, recursive = TRUE)
  dir.create(file.path(pcs_csv_folder), showWarnings = FALSE, recursive = TRUE)
  dir.create(file.path(coord_csv_folder), showWarnings = FALSE, recursive = TRUE)
  dir.create(file.path(reading_h5_folder), showWarnings = FALSE, recursive = TRUE)
  
  pcs_csv_path <- sprintf("%s/pcs_%d_from_bayesSpace_top_2000_HVGs.csv"
                          ,pcs_csv_folder
                          ,n_PCs)
  coord_csv_path <- sprintf("%s/coordinates.csv",coord_csv_folder)
  mclust_csv_path <- sprintf("%s/mclust_result.csv",preprocessed_data_sample_folder)
  
  write.csv(pcs,pcs_csv_path)
  write.csv(coordinates,coord_csv_path)
  write.csv(mclust_result,mclust_csv_path)
  file.copy(list.files(dir_name, full.names = TRUE), reading_h5_folder, recursive = TRUE)
  
  print("DONE!!!!")
}
















