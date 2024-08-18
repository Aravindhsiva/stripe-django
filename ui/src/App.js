import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import React from 'react';
import { CheckoutForm } from './CheckoutForm';

// Make sure to call `loadStripe` outside of a component’s render to avoid
// recreating the `Stripe` object on every render.
const stripePromise = loadStripe(process.env.REACT_APP_PUB_KEY);

function App() {

  const options = {
    // passing the SetupIntent's client secret
    clientSecret:'seti_1PpCtBIbUvrwkR54dSnMnZeU_secret_Qga3uISkuat877QLzJATJsOyXhHwRuf',
    // Fully customizable with appearance API.
    appearance: {},
  };

  return (
    <Elements stripe={stripePromise} options={options}>
       <CheckoutForm/>
    </Elements>
  );
};

export default App;
