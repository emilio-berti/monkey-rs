# Remote Sensing For Monkeys

Just a code template I can clone when needed.

# MODIS

`MODIS` contains utilities to download MODIS data using `luna`. You need to store your NCEI credentials in this folder to use it.
```
writeRDS(c(username = <username>, password = <password>), "credentials.rds")
```

## download-LST.R

This is best called in non-interactive mode.
You need to pass four arguments:

  1. The start date 
  2. The end date
  3. The region of interest (a .shp file)
  4. The name of the directory where to download the data

For instance, `Rscript --vanilla download-LST.R 2024-08-01 2024-08-31 italy.shp LST` will download MODIS data for August 2024 for Italy in the `LST` folder. If `LST` does not exist, it will create it.

## merge-LST.R

The downloaded files are named something like `MOD11A1.A2024219.h19v04.061.2024222010545.hdf`.

  - `MOD11A1.A` is the name of the MODIS product with LST
  - `2024219` indicate the year and day of the year of the file
  - `h19v04` is the hour and minute of collection
  - `061` is the version of the MODIS product
  - `2024222010545` is the product name and time

In the example above, for the day 219 (August 6), there are for files:

 - `MOD11A1.A2024219.h18v04.061.2024222010522.hdf`
 - `MOD11A1.A2024219.h18v05.061.2024222010530.hdf`
 - `MOD11A1.A2024219.h19v04.061.2024222010545.hdf`
 - `MOD11A1.A2024219.h19v05.061.2024222010512.hdf`

This can be merged using `merge-LST.R`, also best to be called in non-interactive mode.
You need to pass one arguments:

  1. The name of the directory where the data was downloaded

For example, `Rscript --vanilla marge-LTS.R LST`
The merged rasters will be saved as `.tif` rather than `.hdf`.

## VIIRS

`VNP21A1D.A2024217.h19v05.002.2024221202133.h5`

[remotesensing.py](remotesensing.py) is the class template.

[mols-ndvi.py](mols-ndvi.py) is a workflow template.

