from pyspark.ml import PipelineModel

# Load pre-trained model
def load_model():
    return PipelineModel.load("saved_models/status_flag_model")

# Apply model on DataFrame
def predict(df, model):
    return model.transform(df)
