import numpy as np
import matplotlib.pyplot as plt

from reaction_kinetics.reaction import Reaction
from reaction_kinetics.reactor import RecyclePlugFlow


final_conversion = 0.5
R = 10
Ca0 = 10

# Create a scatter plot of concentration vs reaction rate
reactor1 = RecyclePlugFlow(order_of_reaction=1, kinetic_constant=6)
# avarage time
av_rate = reactor1.avarage_rate(R, final_conversion, Ca0)
print("av rate:", av_rate)
# Residence time
tau = reactor1.residence_time(R, Ca0, final_conversion)
print("residence time", tau)
