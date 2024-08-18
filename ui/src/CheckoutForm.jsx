import { PaymentElement, useElements, useStripe } from '@stripe/react-stripe-js';
import React, { useState } from 'react';

export const CheckoutForm = () => {

    const [processing, setProcessing] = useState(false);

    const elements = useElements();
    const stripe = useStripe();
    return (
        <form onSubmit={async e => {
            e.preventDefault();
            setProcessing(true);
            const { error, setupIntent } = await stripe.confirmSetup({
                elements, confirmParams: {
                    return_url: `${window.location.origin}/success`,
                },
                redirect:"if_required"
            });
            setProcessing(false);
            if (error) {
                debugger;
            } else {
                console.log(setupIntent);
                alert(setupIntent.status);
            }
        }}>
            <PaymentElement />
            <button className='btn btn-primary'>{processing ? "Processing" : "Submit"}</button>
        </form>
    )
}
