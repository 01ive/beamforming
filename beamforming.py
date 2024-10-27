import numpy as np

def create_IQ_signal(frequence, time_vector):
    return np.exp(2j * np.pi * frequence * time_vector)

def create_steering_vectors(antena_rx_nbr, antena_spacing, theta):
    return np.exp(-2j * np.pi * antena_spacing * np.arange(antena_rx_nbr) * np.sin(theta))

def generate_noise_on_signal(signals):
    antena_rx_nbr = signals.shape[0]
    N = signals.shape[1]
    n = np.random.randn(antena_rx_nbr, N) + 1j*np.random.randn(antena_rx_nbr, N)
    return signals + 0.5*n

def beamforming(signals, steering_vectors):
    return steering_vectors.conj().T @ signals