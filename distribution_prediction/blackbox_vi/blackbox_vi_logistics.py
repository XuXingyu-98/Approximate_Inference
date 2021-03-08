import jax.numpy as np
import jax
import numpy as onp
from jax import grad

from distribution_prediction.blackbox_vi.utils_plots import plot_vi_logistics


def sigmoid(X: np.ndarray,
            theta: np.ndarray
            ) -> np.ndarray:
    """
    :param X: matrix of shape N * P containing a data point per row
    :param theta: matrix of parameters: shape: 1 * P or M * P
    :return: (matrix of size N * 1 or N * M) : the sigmoid function applied to every element of the matrix X.dot(theta.T)
    """
    return np.clip(1 / (1 + np.exp(- np.dot(X, theta.T))), 1e-5, 1 - 1e-5)


def kl_div(mu: np.ndarray,
           A: np.ndarray,
           sigma_prior: float
           ) -> float:
    """
    Computes the KL divergence between
    - the approximated posterior distribution N(mu, Sigma)
    - and the prior distribution on the parameters N(0, (sigma_prior ** 2) I)

    Instead of working directly with the covariance matrix Sigma, we will only deal with its Cholesky matrix A:
    It is the lower triangular matrix such that Sigma = A * A.T

    :param mu: mean of the posterior distribution approximated by variational inference
    :param A: Choleski matrix such that Sigma = A * A.T,
    where Sigma is the coveriance of the posterior distribution approximated by variational inference.
    :param sigma_prior: standard deviation of the prior on the parameters. We put the following prior on the parameters:
    N(mean=0, variance=(sigma_prior**2) I)
    :return: the value of the KL divergence
    """
    # TODO
    d = A.shape[0]

    x = -2 * np.log(np.prod(np.diagonal(A))) + 2 * np.log(sigma_prior) * d - d
    y = (np.linalg.norm(A, ord='fro') ** 2) / (sigma_prior ** 2)
    z = np.linalg.norm(mu, ord='fro') ** 2 / (sigma_prior ** 2)

    return 0.5 * (x + y + z)


def expected_log_likelihood(mu: np.ndarray,
                            A: np.ndarray,
                            epsilon: np.ndarray,
                            X: np.ndarray,
                            y: np.ndarray
                            ) -> float:
    """
    :param mu: mean of the posterior distribution approximated by variational inference
    :param A: Choleski matrix such that Sigma = A * A.T,
    where Sigma is the coveriance of the posterior distribution approximated by variational inference.
    :param epsilon: The samples from N(0, I) that will be used to generate samples from
    the approximated posterior N(mu, Sigma) by using the matrix A and the vector mu
    :param X: data points of shape (N, 2) where N is the number of data points. There is one data point per row
    :param y: column vector of shape (N, 1) indicating the class of p. for each point, y_i = 0 or 1.
    In addition, y_i = 1 is equivalent to "x_i is in C_1"
    :return: The expected log-likelihood. That expectation is calculated according to the approximated posterior
    N(mu, Sigma) by using the samples in epsilon.
    """
    S = len(epsilon)
    N = X.shape[0]
    """""
    theta = []
    
    for i in range(len(epsilon)):
        print("iteration: ", i)
        theta_n = mu + A @ epsilon[i].reshape(2, 1)
        theta.append(theta_n.reshape(2, ))

    theta = np.array(theta)
    mu_b = sigmoid(X, theta)
    """""
    theta = A @ epsilon.T
    theta = theta + mu
    theta = theta.T
    print(theta.shape)

    mu_b = sigmoid(X, theta)
    print("sigmoid done")

    preds = 0
    """""
    for i in range(N):
        for j in range(S):
            if y[i] == 1:
                preds += np.log(mu_b[i, j])
            else:
                preds += np.log(1 - mu_b[i, j])
    print("preds done")
    """""
    idx = np.argwhere(y > 0)
    for i in idx:
        mu_n = mu_b[i, :]
        mu_n = np.log(mu_n)
        preds += np.sum(mu_n)

    idx = np.argwhere(y == 0)
    for i in idx:
        ones = np.ones(S)
        mu_n = ones - mu_b[i, :]
        mu_n = np.log(mu_n)
        preds += np.sum(mu_n)

    preds /= S

    return preds
    # TODO


def variational_inference_logistics(X: np.ndarray,
                                    y: np.ndarray,
                                    num_samples_per_turn: int,
                                    sigma_prior: float,
                                    number_iterations: int = 1000):
    """
    This function performs a variational inference procedure.

    Here we consider that our parameters follow a normal distribution N(mu, Sigma).
    Instead of working directly with the covariance matrix Sigma, we will only deal with its Cholesky matrix A:
    It is the lower triangular matrix such that Sigma = A * A.T

    At the end of each step, it yields the following elements (in this order):
    - the new estimated mu
    - the new estimated Sigma
    - the new estimated lower triangular matrix A (verifying A * A.T = Sigma)
    - mu_grad: the gradient of the marginal likelihood bound with respect to mu
    - A_grad: the gradient of the marginal likelihood bound with respect to A
    - epsilon: The samples from N(0, I) that were used to generate the samples from N(mu, Sigma)

    :param X: data points of shape (N, 2) where N is the number of data points. There is one data point per row
    :param y: column vector of shape (N, 1) indicating the class of p. for each point, y_i = 0 or 1.
    In addition, y_i = 1 is equivalent to "x_i is in C_1"
    :param num_samples_per_turn: number of samples of parameters to use at each step of the Blackbox Variational
    Inference Algorithm
    :param sigma_prior: standard deviation of the prior on the parameters. We put the following prior on the parameters:
    N(mean=0, variance=(sigma_prior**2) I)
    :param number_iterations: number of Blackbox Variational Inference steps before stopping
    """
    P = X.shape[1]

    counter = 0
    mu = np.zeros(shape=(1, P)) + 0.01
    A = np.identity(P)

    # Matrix used to make sure that the elements on the diagonal of A remain superior to 1e-5 at every step
    T = onp.full_like(A, -float('inf'))
    for i in range(P):
        T[i, i] = 1e-5

    epsilon = None
    mu_grad = None
    A_grad = None
    print("task 8 starts")

    while counter < number_iterations:
        print(counter)
        mu_old = mu
        A_old = A
        #############################
        # TODO : Complete Here for computing epsilon, mu_grad and A_grad
        mu_grad_kl, A_grad_kl = grad(kl_div, argnums=(0, 1))(mu, A, sigma_prior)

        A_grad_ll = np.zeros_like(A)
        mu_grad_ll = np.zeros_like(mu)

        epsilon = onp.random.randn(num_samples_per_turn, P)

        mu_grad_ll_temp, A_grad_ll_temp = grad(expected_log_likelihood, argnums=(0, 1))(mu, A, epsilon, X, y)
        A_grad_ll += A_grad_ll_temp

        mu_grad_ll += mu_grad_ll_temp

        A_grad = -1 * A_grad_kl + A_grad_ll
        mu_grad = -1 * mu_grad_kl + mu_grad_ll
        #############################

        # Performing a gradient descent step on A and mu
        # (we make sure that the elements on the diagonal of A remain superior to 1e-5)
        A = np.maximum(A + (1. / (10 * counter + 100.)) * np.tril(A_grad), T)
        mu = mu + (1. / (10 * counter + 100.)) * mu_grad

        counter += 1
        if counter % 1 == 0:
            # Printing the highest change in parameters at that iteration
            print(f"counter: {counter} - {onp.max((onp.linalg.norm(mu_old - mu), onp.linalg.norm(A_old - A)))}\r")

        yield mu, A.dot(A.T), A, mu_grad, A_grad, epsilon


if __name__ == '__main__':
    plot_vi_logistics(interactive=True,
                      interval_plot=1,
                      number_points_per_class=25,
                      number_iterations=1000)
