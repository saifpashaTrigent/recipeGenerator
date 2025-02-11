import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from functions.product_details import product_categories, product_images
from functions.doc_processor import (
    get_pdf_texts,
    create_knowledge_hub,
    generate_recipe,
    generate_product_description,
    stream_data,
    generate_recipe_image
)
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)


async def main():
    st.set_page_config(page_title="Recipe Generator", page_icon="🍲", layout="wide")

    st.title("Recipe Generator")
    st.markdown(
        """
        Welcome to Canprev's Recipe Generator! This tool generates recipes or product insights based on our curated PDF files.
        Select your product options from the sidebar and then click **Generate Recipe**.
        """
    )

    # Sidebar: Product selection and Build/Update Knowledge Base
    with st.sidebar:
        st.image(CANPREV_IMAGE_PATH, width=160)
        st.header("Select Products")
        selected_category = st.selectbox(
            "Product Category:", list(product_categories.keys())
        )
        selected_product = st.selectbox(
            "Product Name:", product_categories[selected_category]
        )

        # Display product image in sidebar if available.
        image_path_sidebar = product_images.get(selected_product)
        if image_path_sidebar and os.path.exists(image_path_sidebar):
            st.image(image_path_sidebar, use_container_width=True)
        else:
            st.warning(f"Image not found: {image_path_sidebar}")

        if st.button("Build/Update Knowledge Base"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")

    # Optional instructions: how the user wants the recipe to be.
    optional_instructions = st.text_area(
        "Optional: Describe how you want the recipe to be",
        placeholder="e.g. healthy, vegan, spicy, low-calorie, extra protein...",
        height=100,
    )

    # When "Generate Recipe" is clicked.
    if st.button("Generate Recipe"):
        with st.spinner("Generating a recipe...",show_time=True):
            final_query = selected_product
            if optional_instructions.strip():
                final_query += " " + optional_instructions.strip()
            recipe_text = await generate_recipe(final_query)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### Recipe Details")
            st.write_stream(stream_data(recipe_text["output"]))
            
        with col2:
            st.markdown("### Recipe Image")
            recipe_image_url = await generate_recipe_image(recipe_text["output"])
            if recipe_image_url:
                st.image(recipe_image_url, caption=selected_product, width=400)
            
        st.markdown("### Product Image")
        image_path_main = product_images.get(selected_product)
        if image_path_main and os.path.exists(image_path_main):
            st.image(image_path_main, caption=selected_product, width=350)
        else:
            st.warning(f"Image not found: {image_path_main}")
        st.markdown("---")
        st.markdown("### Product Description")
        description = await generate_product_description(selected_product)
        st.write_stream(stream_data(description))


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
