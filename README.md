# Friend-Suggest-Algorithm
Third party implementation of the paper [Suggesting Friends using the Implicit Social Graph](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36371.pdf) for a user egocentric network. 

# Usage
```
python fsa.py
```

# Sample Data (for Evaluation)
A custom/internal email dataset was used in the [original paper](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36371.pdf) to evaluate the algorithm. Since the dataset is not public, the [Enron email dataset](https://www.cs.cmu.edu/~./enron/) was used here. The Enron dataset is a standard public email dataset. You can download the dataset from [here](https://www.cs.cmu.edu/~./enron/enron_mail_20150507.tar.gz). The script `data_loader.py` was specifically implemented to load the some emails (outgoing/incoming) of a single user account from dataset.

# Steps to use the (Enron) Data
- Unzip the downloaded dataset
- From a single user folder, select these four folder: `inbox`, `notes_inbox`, `sent`, `sent_items`
- Copy these four folder to into the `dataset` folder

# Requirements
- Python3

# Note
The code was written with verbosity (in mind) over speed.

# License
- All code in this repository are licensed under the MIT license as specified by the LICENSE file.
