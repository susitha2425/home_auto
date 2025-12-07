from intent_update import load_and_prepare_data, train_model, load_model, predict_intent

def run_prediction(command):
    try:
        model = load_model()
    except FileNotFoundError:
        print(" No saved model found. Training new one...")
        df = load_and_prepare_data("dataset4.csv")
        model = train_model(df)
    return predict_intent(model, command) 

if __name__ == "__main__":
    
    test_command = "fan on"
    
    intent = run_prediction(test_command)
    print(f" Predicted Intent: {intent}")

