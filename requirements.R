mirror <- getCRANmirrors()
# mirror$URL[mirror$Country == "Germany"]
mirror <- mirror$URL[mirror$City == "Leipzig"]

install.packages("RcppArmadillo", repos = mirror)
install.packages("luna", repos = "https://rspatial.r-universe.dev")
