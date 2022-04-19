import os
import shutil
import yaml
import base64
import re
import numpy as np
import pandas as pd
import scipy.stats as ss
import seaborn as sns
import matplotlib.pyplot as plt
from sys import modules
from glob import glob as ls
from sklearn.metrics import accuracy_score, f1_score, precision_score, \
    recall_score
from typing import Tuple, List, Callable


# =============================================================================
# ============================ GENERAL HELPERS ================================
# =============================================================================


def vprint(message: str, 
           verbose: bool) -> None:
    """ Print a message based on the verbose mode.

    Args:
        message (str): Message to be printed.
        verbose (bool): Verbose mode.
    """
    if verbose: 
        print(message)


def exist_dir(dir: str) -> bool:
    """ Check if a directory exists.

    Args:
        dir (str): Directory to be checked.

    Raises:
        NotADirectoryError: Error raised when the directory does not exist.
        
    Returns:
        bool: True if the directory exists, an error is raised otherwise.
    """
    if os.path.isdir(dir):
        return True
    raise NotADirectoryError(f"In exist_dir, directory '{dir}' not found")


def print_list(lst: List[str]) -> None:
    """ Print all the elements inside a list.

    Args:
        lst (List[str]): List to be printed.
    """
    for item in lst:
        print(item)
        
        
def show_dir(dir: str = ".") -> None:
    """ Shows all the files and directories inside the specified directory up 
    to the fourth level deep.

    Args:
        dir (str, optional): Source directory to be listed. Defaults to '.'.
    """
    print(f"{'='*10} Listing directory {dir} {'='*10}")
    print_list(ls(dir))
    print_list(ls(dir + '/*'))
    print_list(ls(dir + '/*/*'))
    print_list(ls(dir + '/*/*/*'))
    print_list(ls(dir + '/*/*/*/*'))
    

def mvdir(source: str, 
          dest: str) -> None:
    """ Move a directory to the specified destination.

    Args:
        source (str): Current directory location.
        dest (str): Directory destination.
        
    Raises:
        OSError: Error raised when the directory cannot be renamed.
    """
    if os.path.exists(source):
        try:
            os.rename(source, dest)
        except:
            raise OSError(f"In mvdir, directory '{source}' could not be moved"
                + f" to '{dest}'")
            
            
def mkdir(dir: str) -> None:
    """ Create a directory. If the directory already exists, deletes it before 
    creating it again.

    Args:
        dir (str): Directory to be created.
        
    Raises:
        OSError: Error raised when the directory cannot not be deleted or 
            created.
    """
    if os.path.exists(dir):
        try:
            shutil.rmtree(dir)
        except:
            raise OSError(f"In mkdir, directory '{dir}' could not be deleted")
    
    try:
        os.makedirs(dir)
    except:
        raise OSError(f"In mkdir, directory '{dir}' could not be created")
 

def load_yaml(file: str) -> dict:
    """ Loads the content of a YAML file.

    Args:
        file (str): File in YAML format.

    Raises:
        OSError: Error raised when the file cannot be opened.

    Returns:
        dict: Content of the YAML file.
    """
    try:
        return yaml.safe_load(open(file, "r"))
    except:
        raise OSError(f"In load_yaml, file '{file}' could not be opened or "
            + f"has wrong format")


def create_path_here(file: str) -> str:
    """ Create the absolute path of the specified file inside this directory.

    Args:
        file (str): File that needs a path.

    Returns:
        str: Absolute path to the specified file.
    """
    curr_dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(curr_dir_path, file)


def natural_sort(text: str) -> list:
    """ Helper to sort a list of strings with digits in natural order. This
    helper should be used as the key parameter in the sorted() function.

    Args:
        text (str): Text to be processed.

    Returns:
        list: Splitted text into words and digits.
    """
    atoi = lambda x: int(x) if x.isdigit() else x
    return [atoi(c) for c in re.split(r"(\d+)", text)]


# =============================================================================
# ========================= SCORE RELATED HELPERS =============================
# =============================================================================


def read_results_file(file: str, dtype) -> np.ndarray:
    """ Read the results of the ingestion program, ground truth or predictions.

    Args:
        file (str): Path to the results file.
        dtype: Data type of the data inside the file.

    Raises:
        Exception: Error raised when the results file cannot be opened.

    Returns:
        np.ndarray: Array of data of the results file.
    """
    try:
        return np.loadtxt(file, dtype=dtype)
    except:
        raise Exception(f"In read_results_file, file '{file}' could not be "
            + f"opened")
    

def get_score() -> Tuple[str, Callable[[np.ndarray, np.ndarray], float]]:
    """ Read the score that should be used to evaluate the submissions.

    Raises:
        NotImplementedError: Error raised when the score is not implemented.

    Returns:
        Tuple[str, Callable[[np.ndarray, np.ndarray], float]]: The first
            element corresponds to the name of the score while the second one
            is the implementation of the score.
    """
    # Read score
    with open(create_path_here("scores.txt"), "r") as f:
        score_name = f.readline().strip()

    # Find score implementation
    try:
        scoring_function = getattr(modules[__name__], score_name)
    except:
        raise NotImplementedError(f"In get_score, '{score_name}' not found")

    # Update score name
    score_name = score_name.replace("_", " ")
    score_name = score_name.title()
    return score_name, scoring_function
        

def mean_confidence_interval(data: list, 
                             confidence: float = 0.95) -> Tuple[float, float]:
    """ Compute the mean and the confidence interval of the specified data.

    Args:
        data (list): List of scores to be used in the calculations.
        confidence (float, optional): Level of confidence that should be used. 
            Defaults to 0.95.

    Returns:
        Tuple[float, float]: The first element corresponds to the mean value of
            the data while the second is the confidence interval.
    """
    n = len(data)
    if n == 0:
        return None, None
    if n > 1:
        mean = np.mean(data)
        se = ss.sem(data)
        conf_int = se * ss.t.ppf((1 + confidence) / 2., n - 1)
    else:
        mean = data[0]
        conf_int = 0.0
    return mean, conf_int


def create_histogram(data: list, 
                     score_name: str, 
                     title: str, 
                     path: str) -> str:
    """ Create, save and load a frequency histogram with the specified data.

    Args:
        data (list): Data to be plotted.
        score_name (str): Score used to compute the data.
        title (str): Title for the histogram.
        path (str): Path to save the histogram.

    Returns:
        str: Frequency histogram.
    """
    sns.set_style('darkgrid')
    
    df = pd.DataFrame(data, columns=["value"])
    
    fig, ax = plt.subplots(figsize=(8,4))
    
    # KDE plot
    sns.set_style('white')
    sns.kdeplot(data=df, x="value", ax=ax, warn_singular=False)
    
    # Histogram plot
    ax2 = ax.twinx()
    sns.histplot(data=df, x="value",  bins=40, ax=ax2)

    # Format axes
    x_min, x_max = np.min(data), np.max(data)
    if not np.isclose(x_min, x_max):
        ax.set_xlim((x_min, x_max))
    ax.set_xlabel(f"Score ({score_name})") 
    ax2.set_ylabel("Frequency")
    ax.set_title(title, size = 17)
    
    # Save and return plot
    fig.savefig(path, dpi=fig.dpi)
    plt.close(fig)
    with open(f"{path}.png", "rb") as image_file:
        histogram = base64.b64encode(image_file.read()).decode('ascii')
    return histogram


def create_heatmap(data: dict, 
                   keys: list, 
                   yticks: list, 
                   score_name: str, 
                   title: str, 
                   path: str) -> str:
    """ Create, save and load a frequency heatmap with the specified data.

    Args:
        data (dict): Data to be plotted.
        keys (list): Keys of the data.
        yticks (list): Labels for the y ticks.
        score_name (str): Score used to compute the data.
        title (str): Title for the heatmap.
        path (str): Path to save the heatmap.

    Returns:
        str: Frequency heatmap.
    """
    # Limits for the heatmap
    minimum = np.inf
    maximum = -np.inf
    for key in keys:
        minimum = min(np.min(data[key][score_name]), minimum)
        maximum = max(np.max(data[key][score_name]), maximum)    
    
    # Heatmap data
    bins = np.linspace(minimum, maximum, 11)
    heatmap = [np.histogram(data[key][score_name], bins=bins)[0] for key in 
        keys]
      
    # Plot
    fig, ax = plt.subplots(figsize=(8,4))
    sns.heatmap(heatmap, cmap="Blues", linewidths=.2, yticklabels=yticks)
    ax.set_xticks(np.arange(len(bins)), labels=np.round(bins, 2))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", 
        rotation_mode="anchor")
    ax.set_xlabel(f"Score ({score_name})") 
    ax.set_title(title, size = 17)
    fig.tight_layout()
    
    # Save and return plot
    fig.savefig(path, dpi=fig.dpi)
    plt.close(fig)
    with open(f"{path}.png", "rb") as image_file:
        heatmap = base64.b64encode(image_file.read()).decode('ascii')
    return heatmap


# =============================================================================
# ============================== SCORE FUNCTIONS ==============================
# =============================================================================


def accuracy(y_true: np.ndarray, 
             y_pred: np.ndarray) -> float:
    """ Compute the accuracy of the given predictions.

    Args:
        y_true (np.ndarray): Ground truth labels.
        y_pred (np.ndarray): Predicted labels.

    Raises:
        Exception: Exception raised when the accuracy cannot be computed.

    Returns:
        float: Accuracy of the predictions.
    """
    y_pred = np.argmax(y_pred, axis=1)
    try:
        return accuracy_score(y_true, y_pred)
    except Exception as e:
        raise Exception(f"In accuracy, score cannot be computed. Detailed "
            + f"error: {repr(e)}")
    

def macro_f1_score(y_true: np.ndarray, 
                   y_pred: np.ndarray) -> float:
    """ Compute the macro averaged f1 score of the given predictions.

    Args:
        y_true (np.ndarray): Ground truth labels.
        y_pred (np.ndarray): Predicted labels.

    Raises:
        Exception: Exception raised when the macro averaged f1 score cannot be 
            computed.

    Returns:
        float: Macro averaged f1 score of the predictions.
    """
    y_pred = np.argmax(y_pred, axis=1)
    try:
        return f1_score(y_true, y_pred, average = "macro", zero_division = 0)
    except Exception as e:
        raise Exception(f"In macro_f1_score, score cannot be computed. "
            + f"Detailed error: {repr(e)}")
        

def macro_precision(y_true: np.ndarray, 
                    y_pred: np.ndarray) -> float:
    """ Compute the macro averaged precision of the given predictions.

    Args:
        y_true (np.ndarray): Ground truth labels.
        y_pred (np.ndarray): Predicted labels.

    Raises:
        Exception: Exception raised when the macro averaged precision cannot be 
            computed.

    Returns:
        float: Macro averaged precision of the predictions.
    """
    y_pred = np.argmax(y_pred, axis=1)
    try:
        return precision_score(y_true, y_pred, average = "macro", 
            zero_division = 0)
    except Exception as e:
        raise Exception(f"In macro_precision, score cannot be computed. "
            + f"Detailed error: {repr(e)}")
        
        
def macro_recall(y_true: np.ndarray, 
                 y_pred: np.ndarray) -> float:
    """ Compute the macro averaged recall of the given predictions.

    Args:
        y_true (np.ndarray): Ground truth labels.
        y_pred (np.ndarray): Predicted labels.

    Raises:
        Exception: Exception raised when the macro averaged recall cannot be 
            computed.

    Returns:
        float: Macro averaged recall of the predictions.
    """
    y_pred = np.argmax(y_pred, axis=1)
    try:
        return recall_score(y_true, y_pred, average = "macro", 
            zero_division = 0)
    except Exception as e:
        raise Exception(f"In macro_recall, score cannot be computed. Detailed "
            + f"error: {repr(e)}")


def compute_all_scores(y_true: np.ndarray, 
                       y_pred: np.ndarray) -> dict:
    """ Computes the accuracy, macro averaged f1 score, macro averaged 
    precision and macro averaged recall of the given predictions.

    Args:
        y_true (np.ndarray): Ground truth labels.
        y_pred (np.ndarray): Predicted labels.

    Returns:
        dict: Dictionary with all the scores.
    """
    scoring = {
        "Accuracy": accuracy,
        "Macro F1 Score": macro_f1_score,
        "Macro Precision": macro_precision,
        "Macro Recall": macro_recall
    }
    scores = dict()
    for key in scoring.keys():
        scoring_function = scoring[key]
        scores[key] = scoring_function(y_true, y_pred)
    return scores