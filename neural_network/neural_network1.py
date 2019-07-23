import numpy as np
from .functions import sigmoid, relu, quadratic_cost

class TrainingError(Exception):
    pass

def quadratic_cost(y, y_hat, derivative=False):
    #calculate squared error for a single observation (y) and prediction (y_hat)
    if derivative:
        return (y_hat - y)
    else:
        return 0.5 * (y - y_hat)**2

class NeuralNetwork:
    activation_functions = {'relu': relu, 'sigmoid': sigmoid}

    def __init__(self, sizes, activations=None):
        self.sizes = sizes
        self.weights = self.init_weights()
        if activations is None:
            self.activations = ["sigmoid" for i in range(1, len(sizes))] + ["sigmoid"]
        else:
            self.activations = activations
        #no bias needed for first layer
        self.biases = [np.random.randn(s,1) * 0.1 for s in sizes[1:]]

    def init_weights(self):
        input_sizes = self.sizes[:-1]
        output_sizes = self.sizes[1:]
        weight_dims = list(zip(output_sizes, input_sizes))
        #at layer l, weight[j][k] is the weight from the 
        # kth neuron in the layer l-1 to the jth neuron in layer l
        weights = [np.random.randn(j,k) for j,k in weight_dims]
        #normalize variance by size of inputs
        weights = [W / (W.shape[1]**(0.5)) for W in weights]
        return weights

    def forward_prop_layer(self, layer_number, A):
        #A the "activated" matrix input from previous layer
        W = self.weights[layer_number]
        b = self.biases[layer_number]
        Z = np.dot(W, A) + b
        act_fn = self.activations[layer_number]
        activate = self.activation_functions[act_fn]
        A = activate(Z)
        return A,Z

    def feed_forward(self, X):
        A = X
        for l in range(0, len(self.sizes) - 1):
            A,Z = self.forward_prop_layer(l,A)
        return A

    def update_batch(self, X, Y, learning_rate):
        #X,Y are mini batches of training X and Y
        m = X.shape[0]
        eta = learning_rate
        #Sum the cost function gradient (w.r.t weights, biases) for each 
        #data point in the mini-batch
        del_weights, del_biases = self.backpropagate(X,Y,m)
        for l in range(len(self.sizes) - 1):
            self.weights[l] -= eta * del_weights[-l-1]
            self.biases[l] -= eta * del_biases[-l-1]
        return

    def backpropagate(self, X, Y, m):
        del_weights = []
        del_biases = []
        #weighted inputs into neuron
        zs = []
        #activated outputs from neuron 
        #set activation of 0th layer: it's the input!
        A = X.T
        activations = [A]
        #feed forward and store As, Zs
        for l in range(0, len(self.sizes) - 1):
            A,Z = self.forward_prop_layer(l, A)
            activations.append(A)
            zs.append(Z)

        #backward pass
        #errors is an (n,m) array for each layer
        #n number of neurons in the layer, m the number of samples in mini-batch
        d_cost = quadratic_cost(Y.T, activations[-1], derivative = True)
        errors = d_cost * sigmoid(zs[-1], derivative = True)

        #take the average of sample errors to get bias gradient
        del_biases = [errors.sum(axis=1).reshape(-1,1) / m]

        #multiply error by activations of previous layer
        #then take average across m samples to get weight gradient
        del_weights = [(errors @ activations[-2].T / m)]
        for l in range(2, len(self.sizes)):
            act_fn = self.activations[-l]
            activate = self.activation_functions[act_fn]
            errors = (self.weights[-l+1].T @ errors) * \
                    activate(zs[-l], derivative = True)
            del_bias = (errors.sum(axis=1).reshape(-1,1)) / m
            del_biases.append(del_bias)
            del_weight = (errors @ activations[-l-1].T) / m
            del_weights.append(del_weight)
        
        return del_weights, del_biases 

    def train(self, training_data, epochs, learning_rate,
            batch_size = -1, test_data = None, evaluate_per=100):
        #training_data is a tuple (X,Y) of inputs and observations
        if training_data[0].shape[0] != training_data[1].shape[0]:
            raise TrainingError("X and Y have different sample sizes!")
        elif training_data[0].shape[1] != self.sizes[0]:
            raise TrainingError("{} feature(s) in inputs, expected {}"\
                    .format(training_data[0].shape[1], self.sizes[0]))
        elif training_data[1].shape[1] != self.sizes[-1]:
            raise TrainingError("{} class(es) in outputs, expected{}"\
                    .format(training_data[1].shape[1], self.sizes[-1]))

        #number observations in sample
        n = training_data[0].shape[0]
        if batch_size < 0:
            batch_size = n
        for i in range(epochs):
            np.random.seed(3 + i) 
            #shuffle the index
            idx = np.random.permutation(n)
            X = training_data[0][idx].copy()
            Y = training_data[1][idx].copy() 
            for j in range(0, n, batch_size):
                X_batch = X[j: j + batch_size]
                Y_batch = Y[j: j + batch_size]
                self.update_batch(X_batch, Y_batch, learning_rate)
            if (test_data is not None) and not ((i+1) % evaluate_per):
                mse, n_correct = self.evaluate(test_data)
                n_test = test_data[0].shape[0]
                print("Evaluating Epoch {}".format(i+1))
                print("--> MSE: {:.2f}".format(mse))
                print("--> Correct prediction: {} / {}".format(n_correct, n_test))
                print("----> {:.2f}%".format(100 * n_correct / n_test))

    def evaluate(self, test_data):
        X,Y = test_data
        n = X.shape[0]
        Y_hat = self.feed_forward(X.T).T
        mse = np.sum(np.linalg.norm(quadratic_cost(Y_hat, Y), axis=1)) / n
        mse = np.sum(quadratic_cost(Y_hat, Y)) / n
        prediction = Y_hat.copy()
        labels = Y
        #single class classification:
        if labels.shape[1] == 1:
            prediction[prediction > 0.5] = 1
            prediction[prediction <= 0.5] = 0
        else:
            prediction = np.argmax(Y_hat, axis=1)
            labels = np.argmax(Y, axis=1)    
        n_correct = (prediction==labels).sum()
        return mse, n_correct

