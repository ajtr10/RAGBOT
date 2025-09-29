#!/usr/bin/env python3
"""
Test script to verify Pinecone integration
Run this to test if Pinecone is properly configured
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

def test_pinecone_connection():
    """Test Pinecone API connection and index access"""
    try:
        # Get API key from environment
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            print("❌ PINECONE_API_KEY not found in environment variables")
            return False
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"✅ Successfully connected to Pinecone")
        print(f"📊 Available indexes: {[idx.name for idx in indexes.indexes]}")
        
        # Check if our target index exists
        index_name = "rag-minilm-384"
        if index_name in [idx.name for idx in indexes.indexes]:
            print(f"✅ Index '{index_name}' exists")
            
            # Get index stats
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"📈 Index stats: {stats}")
        else:
            print(f"⚠️  Index '{index_name}' does not exist yet (will be created on first upload)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Pinecone Integration...")
    print("=" * 50)
    
    success = test_pinecone_connection()
    
    if success:
        print("\n✅ Pinecone integration test passed!")
        print("🚀 Your RAG bot is ready to use Pinecone!")
    else:
        print("\n❌ Pinecone integration test failed!")
        print("📝 Please check your PINECONE_API_KEY and try again.")
