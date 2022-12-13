import warnings
warnings.simplefilter('ignore')


def print_progress(progress, goal):
    LENGTH = 50

    rate = progress / goal
    percent = '{:.2%}'.format(rate)

    message = (" " if progress == goal else "*") + " [" + '█' * int(rate * LENGTH) + ' ' * \
        int((1-rate) * LENGTH) + "]" + f" {progress}/{goal} {percent} "
    print("\r" + message, end="")
