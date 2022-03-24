
prince_ij.csv: User judgments on the usefulness of PRINCE explanations
credpaths_ij.csv: User judgments on the usefulness of CredPaths explanations

Each file contains three lines corresponding to the judgments of one user for one HIT. Each HIT contains 20 data points. 

***********************
Description of fields: 

"Description": Description of the task

"WorkerType": This field has two values, "good_worker" and "bad_worker" set based on the worker's response to the honeypots.  A bad worker falls for the honeypot. 

"Input.former_rec_i": The ith recommendation item to be explained. 

"Input.honey_pot_i": A binary filed, where value 1 shows that the ith explanation is a honeypot. 

"Input.rep1_i": The item that replaces the top recommendation after removing PRINCE explanation  

"Answer.useful_i": User's judgment on the usefulness on a scale of 1 to 3

"Answer.text_i": User's comments justifying their judgment. 

"Explanation_i": Explanation for the ith recommendation. 
