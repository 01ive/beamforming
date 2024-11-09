import numpy as np

def create_IQ_signal(frequence: 'Hz', time_vector: 'list of time axis values') -> 'Signal in Euler form':
    """
    Create complex signal at frequence in Euler form
    """
    return np.exp(2j * np.pi * frequence * time_vector)

def create_steering_vectors(antena_rx_nbr: 'Number of antennas to manage', 
                            antena_spacing: 'Space between 2 antennas', 
                            theta: 'Angle between Rx signal and antenas plan') -> 'Matrix of delays in Euler form':
    """
    Create delays matrix in Euler form
    """
    return np.exp(-2j * np.pi * antena_spacing * np.arange(antena_rx_nbr) * np.sin(theta))

def generate_noise_on_signal(signals: 'Input signal matrix') -> 'Matrix of noisy signals':
    """
    Generate some noise on inputs signals
    """
    antena_rx_nbr = signals.shape[0]
    N = signals.shape[1]
    n = np.random.randn(antena_rx_nbr, N) + 1j*np.random.randn(antena_rx_nbr, N)
    return signals + 0.5*n

def beamforming(signals: 'Input signal matrix', steering_vectors:'Delay matrix for each antenas') -> 'Beam matrix':
    """
    Calculate beam. Use conjugate to reverse delay.
    """
    return steering_vectors.conj().T @ signals

def calculate_beam(tx_signal: 'Real signals seen by antenas', 
                   antena_rx_nbr: 'Number of antennas to manage', 
                   antena_spacing: 'Space between 2 antennas', 
                   theta: 'Angle between Rx signal and antenas plan') -> 'Energy level by angle':
    """
    Calculate N beams on antenas plan and calculate energy for each beam
    """
    steering_vectors = create_steering_vectors(antena_rx_nbr, antena_spacing, np.radians(theta))

    steering_vectors = steering_vectors.reshape(-1,1)
    tx_signal = tx_signal.reshape(1,-1)
    rx_signals = steering_vectors * tx_signal

    rx_signals = generate_noise_on_signal(rx_signals)

    theta_scan = np.linspace(-1*np.pi, np.pi, 1000)
    results = list()
    for theta_i in theta_scan:
        w = create_steering_vectors(antena_rx_nbr, antena_spacing, theta_i)
        X_weighted = beamforming(rx_signals, w)
        results.append(10*np.log10(np.var(X_weighted)))
    results -= np.max(results)
    return results