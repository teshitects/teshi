## Test Case Name

Store_HomePage_Internationalization

## Number

Store_FirstPage_i18n

## Preconditions

1. Device is connected to network
2. Software is opened

## Operation Steps

1. Enhook software set to Chinese, click "Store" interface
2. Enhook software set to English, click "Store" interface

## Expected Results

1. Embedded WebView displays in Chinese
2. Embedded WebView displays in English

## Notes

---

## Test Case Name

Store_Offline_Message

## Number

Store_Offline_Message

## Preconditions

1. Device is not connected to network
2. Software is opened

## Operation Steps

1. Disconnect network connection
2. Open software
3. Click "Store" interface

## Expected Results

1. Display network disconnection prompt message
2. Interface friendly prompts user to check network connection

## Notes

Need to test prompt message display under different network states