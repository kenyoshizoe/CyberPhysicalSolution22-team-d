import math
import random
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.model_selection import train_test_split

import numpy as np
try:
    import cPickle as pickle
except:
    import pickle

# https://scikit-learn.org/stable/modules/classes.html#module-sklearn.linear_model
# https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html
# https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
# https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html

def fit_LinearRegression( X, Y, W=None ):
    model = LinearRegression()
    model.fit( X, Y, W )
    return model

def fit_RidgeRegression( X, Y, W=None, alpha = 0 ):
    model = Ridge( alpha=alpha )
    model.fit( X, Y, W )
    return model

def fit_LogisticRegression( X, Y, W=None, C=1 ):
    model = LogisticRegression( C=C )
    model.fit( X, Y, W )
    return model

def predict( model, X ):
    if( hasattr( model, 'predict_proba' ) ):
        pred = model.predict_proba( X )
        pred = pred[:,1]
    else:
        pred = model.predict( X )
    return pred

def ensemble_mean( models, X ):
    Y = None
    for model in models:
        y = predict( model, X )
        if( Y is None ):
            Y = y[:,np.newaxis]
        else:
            Y = np.concatenate( (Y,y[:,np.newaxis]), axis=1 )
    return Y.mean(axis=1)

def save_model( filename, model ):
    pickle.dump(model, open(filename, 'wb'))

def load_model( filename ):
    model = pickle.load(open(filename, 'rb'))
    return model

def rmse( Ytrue, Ypred ):
    mse = mean_squared_error( Ytrue, Ypred )
    return math.sqrt( mse )

def accuracy( Ytrue, Ypred ):
    return accuracy_score( Ytrue, (Ypred>0.5).astype(np.int) )

def shuffle( X, Y ):
    ind = list(range(Y.size))
    random.shuffle(ind)
    return X[ind,:], Y[ind]

def class_balanced_split( X, Y, train_size_per_class):
    ind0 = (Y == 0)
    ind1 = (Y == 1)

    Xtrain0, Xtest0, Ytrain0, Ytest0 = train_test_split( X[ind0,:], Y[ind0], train_size=train_size_per_class, test_size=Y[ind0].shape[0]-train_size_per_class )
    Xtrain1, Xtest1, Ytrain1, Ytest1 = train_test_split( X[ind1,:], Y[ind1], train_size=train_size_per_class, test_size=Y[ind1].shape[0]-train_size_per_class )

    Xtrain = np.concatenate( (Xtrain0, Xtrain1), axis=0 )
    Ytrain = np.concatenate( (Ytrain0, Ytrain1), axis=0 )
    Xtest = np.concatenate( (Xtest0, Xtest1), axis=0 )
    Ytest = np.concatenate( (Ytest0, Ytest1), axis=0 )

    Xtrain, Ytrain = shuffle( Xtrain, Ytrain )
    Xtest, Ytest = shuffle( Xtest, Ytest )

    return Xtrain, Xtest, Ytrain, Ytest

if( __name__ == '__main__' ):
    from sklearn.utils import shuffle
    filename = 'regression.pkl'

    train = np.load('../dog-vs-cat/imgs_code/train.npz')
    X=train['X']
    Y=train['Y']

    X, Y = shuffle( X, Y )

    Xtrain, Xtest, Ytrain, Ytest = class_balanced_split(X, Y, 512)

    print( Ytrain.shape[0], np.mean( Ytrain ) )
    print( Ytest.shape[0], np.mean( Ytest ) )
    print()

    Ypred = np.random.rand( Ytest.shape[0] )
    print( accuracy( Ytest, Ypred ) )

    model = fit_LinearRegression( Xtrain, Ytrain )
    save_model( filename, model )
    model = load_model( filename )
    Ypred = predict( model, Xtest )
    print( accuracy( Ytest, Ypred ) )

    model = fit_RidgeRegression( Xtrain, Ytrain, alpha=1 )
    save_model( filename, model )
    model = load_model( filename )
    Ypred = predict( model, Xtest )
    print( accuracy( Ytest, Ypred ) )

    model = fit_LogisticRegression( Xtrain, Ytrain, C=1 )
    save_model( filename, model )
    model = load_model( filename )
    Ypred = predict( model, Xtest )
    print( accuracy( Ytest, Ypred ) )


    model = load_model( '../model.pkl' )
    Ypred = predict( model, X )
    print( accuracy( Y, Ypred ) )

    from sklearn.decomposition import PCA

    pca = PCA(n_components=2)
    Xtrain_pca = pca.fit_transform(Xtrain)
    Xtest_pca = pca.transform(Xtest)
    model = fit_LinearRegression( Xtrain_pca, Ytrain )
    Ypred = predict( model, Xtest_pca )
    print( accuracy( Ytest, Ypred ) )

    from sklearn.discriminant_analysis import  LinearDiscriminantAnalysis
    lda = LinearDiscriminantAnalysis(n_components=2)
    Xtrain_lda = lda.fit_transform(Xtrain, Ytrain)
    Xtest_lda = lda.transform(Xtest)
    model = fit_LinearRegression( Xtrain_lda, Ytrain )
    Ypred = predict( model, Xtest_lda )
    print( accuracy( Ytest, Ypred ) )

