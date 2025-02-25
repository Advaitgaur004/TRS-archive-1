import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import Swal from "sweetalert2";
import { useNavigate } from "react-router-dom";

const VerifyOTPPage = () => {
  const [otp, setOTP] = useState("");
  const navigate = useNavigate();
  const { state } = useLocation();

  const email = state?.email;

  const handleVerifyOTP = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      // console.log("heroewkj")
      const response = await fetch("http://127.0.0.1:8000/api/users/verify/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({  
          email: email,
          otp: otp,
        }),
      });
      console.log("email");

      if (response.ok) {
        // OTP verification successful
        Swal.fire({
          title: "OTP Verified Successfully",
          icon: "success",
          toast: true,
          timer: 2000,
          position: "top-right",
          timerProgressBar: true,
          showConfirmButton: false,
        });

        // You can navigate to the login page or perform other actions
        navigate("/login");
      } else {
        // OTP verification failed
        const errorData = await response.json();
        console.log(errorData);
        Swal.fire({
          title: `Error: ${errorData.message}`,
          icon: "error",
          toast: true,
          timer: 2000,
          position: "top-right",
          timerProgressBar: true,
          showConfirmButton: false,
        });
      }
    } catch (error) {
      console.error("Error while verifying OTP:", error);
    }
  };
  return (
    <>
      <div className="mt-48 text-green-500 bg-opacity-0"></div>
      <form
        onSubmit={handleVerifyOTP}
        className="mx-auto mt-16 w-1/5 bg-gradient-to-r from-red-600 to-red-800 text-white p-8 rounded-md shadow-md"
      >
        <label className="block mb-2">OTP:</label>
        <div className="relative mb-4">
          <input
            type="password"
            className="w-full p-2 bg-red-800 border-none rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            required
            onChange={(e) => setOTP(e.target.value)}
            placeholder="Password"
          />

          <div className="absolute w-full left-0 bottom-0 h-1 bg-green-700 transition-colors"></div>
        </div>

        <button
          type="submit"
          className="w-full bg-green-500 hover:bg-green-600 text-white p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          Submit
        </button>
      </form>
    </>
  );
};

export default VerifyOTPPage;
