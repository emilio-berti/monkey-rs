library(terra)
library(luna)

if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) != 1) {
    stop(
      paste(
        "",
        "You need to specify the argument:",
        " - directory where to download the files",
        "",
        "Example:",
        "Rscript --vanilla merge-LST.R LST",
        "",
        sep = "\n"
      )
    )
  }
  datadir <- args[1]
  if (!dir.exists(datadir)) stop("Directory '", datadir, "' does not exist")
} else {
  datadir <- "LST"
}

extract_date <- function(x) {
  if (length(x) > 1) {
    ans <- do.call("rbind", lapply(x, \(f) extract_date(f)))
    rownames(ans) <- x
    return(ans)
  }
  date <- strsplit(x, "[.]")[[1]][2]
  year <- rawToChar(charToRaw(date)[2:5])
  yday <- rawToChar(charToRaw(date)[6:8])
  ans <- c(year = as.numeric(year), yday = as.numeric(yday))
  return(ans)
}

ff <- list.files(datadir, pattern = "[.]h5")
dates <- extract_date(ff)
for (year in unique(dates[, "year"])) {
  message(" - Year: ", year)
  for (day in unique(dates[dates[, "year"] == 2024, "yday"])) {
    message("   - Day: ", day)
    f <- rownames(dates[dates[, "year"] == 2024 & dates[, "yday"] == day, ])
    f <- file.path(datadir, f)
    r <- as.list(rep(NA, length(f)))
    for (i in seq_along(f)) {
      r[[i]] <- suppressWarnings(rast(f[i]))
      ext(r[[i]]) <- modisExtent(f[i])[1, ]
    }
    r <- r |> 
      sprc() |>
      merge()

    r$LST_1KM <- r$LST_1KM * 0.02 - 273.15

    writeRaster(
      r,
      file.path(datadir, paste0(year, "-", day, ".tif")), 
      overwrite = TRUE
    )
    png(
      file.path(datadir, paste0(year, "-", day, ".png")),
      width = 600, height = 600
    )
    plot(r$LST_1KM - 273.15, main = paste0(year, "-", day))
    dev.off()
  }
}
