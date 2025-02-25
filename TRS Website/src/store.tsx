import {  
  legacy_createStore as createStore,
  combineReducers,
  applyMiddleware,
} from "redux";
import { thunk } from "redux-thunk";
import { composeWithDevTools } from "@redux-devtools/extension";

import {
  userVerifyReducer,
  userRegisterReducer,
  userProfileReducer,
  UserLoginReducer,
  userDetailsReducer,
  userUpdateProfileReducer,
  TokenRefreshReducer,
  getAllUsersReducer,
  getAllEditorReducer,
  getAllReviewerReducer,
} from "./reducers/userReducers"; 

import {
  postAssignedReducer,
  postListReducers,
  postUploadReducer,
  userPostReducer,
  getCategoriesReducer,
  getSubCatReducer,
  postUnAssignedPosts,
  post_Upload_ListReducers,
} from "./reducers/postReducers";

import{
editorReviewsReducer,
reviewReviewedReducer,
editReviewReducer,
} from "./reducers/reviewReducer"


import { getNewsReducer } from "./reducers/newsReducer";

const reducer = combineReducers({
  postlist: postListReducers,
  userVerify: userVerifyReducer,
  userRegister: userRegisterReducer,
  userProfile: userProfileReducer,
  userLogin: UserLoginReducer,
  userDetails: userDetailsReducer,
  userUpdateProfile: userUpdateProfileReducer,
  userTokenRefresh: TokenRefreshReducer,
  getallUser: getAllUsersReducer,
  getNews: getNewsReducer,
  getCategories: getCategoriesReducer,
  postUpload: postUploadReducer,
  getuserPosts: userPostReducer,
  assignedPosts: postAssignedReducer,
  getSubCategories: getSubCatReducer,
  unassignedPosts: postUnAssignedPosts,
  getallEditors: getAllEditorReducer,
  getallReviewers:getAllReviewerReducer,
  getallUnderProcessPosts:post_Upload_ListReducers,
  getallReviewsAssignedByEditor:editorReviewsReducer,
  getallReviewedReviews:reviewReviewedReducer,
  editReview:editReviewReducer,
});

const userInfofrom_locStorage = localStorage.getItem("authToken")
  ? JSON.parse(localStorage.getItem("authToken"))
  : null; //this is done to ensure that whenver we reload the it gets info from the local storage

const middleware = [thunk];

const initialState = {
  userLogin: { authToken: userInfofrom_locStorage },
};

const store = createStore(
  reducer,
  initialState,
  composeWithDevTools(applyMiddleware(...middleware))
);

export default store;
