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
    n = np.random.randn(antena_rx_nbr, N) + 1j * np.random.randn(antena_rx_nbr, N)
    return signals + 0.5 * n

def beamforming(signals: 'Input signal matrix', steering_vectors: 'Delay matrix for each antenas') -> 'Beam matrix':
    """
    Calculate beam. Use conjugate to reverse delay.
    """
    return steering_vectors.conj().T @ signals

def calculate_beam(tx_signal: 'Real signals seen by antenas', 
                   antena_rx_nbr: 'Number of antennas to manage', 
                   antena_spacing: 'Space between 2 antennas', 
                   theta: 'Angle between Rx signal and antenas plan',
                   n_scan: int = 1000) -> 'Energy level by angle':
    """
    Calculate N beams on antenas plan with noise (Vectorized version)
    """
    steering_tx = create_steering_vectors(antena_rx_nbr, antena_spacing, np.radians(theta)).reshape(-1, 1)
    rx_signals = steering_tx * tx_signal.reshape(1, -1)
    rx_signals = generate_noise_on_signal(rx_signals)

    theta_scan = np.linspace(-np.pi, np.pi, n_scan)
    n_idx = np.arange(antena_rx_nbr).reshape(-1, 1)
    W = np.exp(-2j * np.pi * antena_spacing * n_idx * np.sin(theta_scan))

    X_weighted = W.conj().T @ rx_signals
    results = 10 * np.log10(np.var(X_weighted, axis=1))
    results -= np.max(results)
    return results

def calculate_ideal_beam(antena_rx_nbr: int, 
                         antena_spacing: float, 
                         theta: float, 
                         n_scan: int = 1000) -> np.ndarray:
    """
    Calcule le facteur de réseau théorique pur (sans bruit) en dB
    """
    steering_tx = create_steering_vectors(antena_rx_nbr, antena_spacing, np.radians(theta)).reshape(-1, 1)
    theta_scan = np.linspace(-np.pi, np.pi, n_scan)
    n_idx = np.arange(antena_rx_nbr).reshape(-1, 1)
    W = np.exp(-2j * np.pi * antena_spacing * n_idx * np.sin(theta_scan))

    # Réponse théorique du filtre spatial adapté
    af = np.abs((W.conj().T @ steering_tx).flatten()) ** 2
    results = 10 * np.log10(af + 1e-12) # +1e-12 pour éviter log10(0)
    results -= np.max(results)
    return results