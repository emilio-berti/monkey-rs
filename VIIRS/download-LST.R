library(terra)
library(luna)

credentials <- readRDS("credentials.rds")

if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) != 4) {
    stop(
      paste(
        "",
        "You need to specify the arguments:",
        " - start_year",
        " - end_year",
        " - region of interest (SpatVector)",
        " - directory where to download the files",
        "",
        "Example:",
        "Rscript --vanilla download-LST.R 2024-08-01 2024-08-31 italy.shp LST",
        "",
        sep = "\n"
      )
    )
  }
  start_date <- args[1]
  end_date <- args[2]
  roi <- vect(args[3])
  outdir <- args[4]
  if (!dir.exists(outdir)) dir.create(outdir)
} else {
  start_date <- '2024-01-01'
  end_date <- '2024-12-31'
  roi <- buffer(vect(cbind(10, 50), crs = crs("EPSG:4326")), 1e6)
  outdir <- "LST"
}

files <- getNASA(
  "VNP21A1D",
  start_date,
  end_date,
  aoi = roi,
  path = outdir,
  version = '002',
  username = credentials["username"],
  password = credentials["password"],
  download = TRUE,
  overwrite = TRUE
)
